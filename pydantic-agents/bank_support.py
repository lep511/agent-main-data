from dataclasses import dataclass
from pydantic import BaseModel, Field
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai import Agent, RunContext, ModelRetry
from datetime import date, datetime
from typing import Optional
import hashlib
import secrets

class AuthenticationError(Exception):
    """Raised when user authentication fails."""
    pass

class SessionManager:
    """Manages user sessions and authentication tokens."""
    
    def __init__(self):
        self._sessions = {}  # token -> session_data
        self._session_timeout = 3600  # 1 hour in seconds
    
    def create_session(self, customer_id: int) -> str:
        """Create a new session token for authenticated user."""
        token = secrets.token_urlsafe(32)
        self._sessions[token] = {
            'customer_id': customer_id,
            'created_at': datetime.now(),
            'last_accessed': datetime.now()
        }
        return token
    
    def validate_session(self, token: str) -> Optional[int]:
        """Validate session token and return customer_id if valid."""
        if not token or token not in self._sessions:
            return None
            
        session = self._sessions[token]
        now = datetime.now()
        
        # Check if session has expired
        if (now - session['last_accessed']).seconds > self._session_timeout:
            del self._sessions[token]
            return None
            
        # Update last accessed time
        session['last_accessed'] = now
        return session['customer_id']
    
    def invalidate_session(self, token: str) -> bool:
        """Invalidate a session token."""
        if token in self._sessions:
            del self._sessions[token]
            return True
        return False

class DatabaseConn:
    """Enhanced database with user authentication capabilities."""

    # Simulated user credentials (in production, use proper password hashing)
    _users = {
        'john_doe': {
            'password_hash': hashlib.sha256('password123'.encode()).hexdigest(),
            'customer_id': 123,
            'name': 'John Doe',
            'is_active': True
        },
        'jane_smith': {
            'password_hash': hashlib.sha256('securepass456'.encode()).hexdigest(),
            'customer_id': 124,
            'name': 'Jane Smith',
            'is_active': True
        }
    }

    @classmethod
    async def authenticate_user(cls, username: str, password: str) -> Optional[int]:
        """Authenticate user and return customer_id if successful."""
        user = cls._users.get(username)
        if not user or not user['is_active']:
            return None
            
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if password_hash == user['password_hash']:
            return user['customer_id']
        return None

    @classmethod
    async def customer_name(cls, *, id: int) -> str | None:
        """Get customer name by ID."""
        for user_data in cls._users.values():
            if user_data['customer_id'] == id:
                return user_data['name']
        return None

    @classmethod
    async def customer_balance(cls, *, id: int, include_pending: bool) -> float:
        """Get customer balance by ID."""
        # Simulated balance data
        balances = {
            123: {'current': 100.00, 'pending': 23.45},
            124: {'current': 250.75, 'pending': 15.30}
        }
        
        if id not in balances:
            raise ModelRetry(f'Customer not found with id: {id!r}')
            
        balance_data = balances[id]
        if include_pending:
            return balance_data['current'] + balance_data['pending']
        else:
            return balance_data['current']

    @classmethod
    async def is_customer_active(cls, *, id: int) -> bool:
        """Check if customer account is active."""
        for user_data in cls._users.values():
            if user_data['customer_id'] == id:
                return user_data['is_active']
        return False

@dataclass
class SupportDependencies:
    customer_id: int
    db: DatabaseConn
    session_token: Optional[str] = None
    is_authenticated: bool = False

class SupportOutput(BaseModel):
    support_advice: str = Field(description='Advice returned to the customer')
    block_card: bool = Field(description='Whether to block their card or not')
    risk: int = Field(description='Risk level of query', ge=0, le=10)
    requires_authentication: bool = Field(
        description='Whether the query requires user authentication',
        default=False
    )

class AuthenticationService:
    """Service for handling user authentication."""
    
    def __init__(self):
        self.session_manager = SessionManager()
        self.db = DatabaseConn()
    
    async def login(self, username: str, password: str) -> Optional[str]:
        """Authenticate user and return session token if successful."""
        customer_id = await self.db.authenticate_user(username, password)
        if customer_id:
            return self.session_manager.create_session(customer_id)
        return None
    
    async def validate_session(self, token: str) -> Optional[int]:
        """Validate session and return customer_id if valid."""
        return self.session_manager.validate_session(token)
    
    def logout(self, token: str) -> bool:
        """Logout user by invalidating session."""
        return self.session_manager.invalidate_session(token)

# Initialize authentication service
auth_service = AuthenticationService()

model = GeminiModel('gemini-2.5-flash', provider='google-vertex')

support_agent = Agent(
    model,
    deps_type=SupportDependencies,
    output_type=SupportOutput,
    instructions=(
        'You are a support agent in our bank. Before providing any sensitive '
        'information or performing account-related actions, you must verify '
        'that the user is properly authenticated. '
        'For unauthenticated users, only provide general information and '
        'ask them to log in for account-specific queries. '
        'Judge the risk level of their query and reply using the customer\'s name '
        'only if they are authenticated.'
    ),
)

@support_agent.instructions
async def check_authentication_status(ctx: RunContext[SupportDependencies]) -> str:
    """Check if user is authenticated and provide appropriate context."""
    if not ctx.deps.is_authenticated:
        return (
            "IMPORTANT: User is NOT authenticated. Do not provide any "
            "account-specific information, balances, or personal details. "
            "Ask them to log in first for account-related queries."
        )
    
    customer_name = await ctx.deps.db.customer_name(id=ctx.deps.customer_id)
    is_active = await ctx.deps.db.is_customer_active(id=ctx.deps.customer_id)
    
    if not is_active:
        return "IMPORTANT: Customer account is inactive. Escalate to supervisor."
    
    return f"User is authenticated. Customer's name is {customer_name!r}"

@support_agent.instructions
def add_the_date() -> str:  
    return f'The current date is {date.today()}.'

@support_agent.tool(retries=2)
async def customer_balance(
    ctx: RunContext[SupportDependencies], include_pending: bool = False
) -> str:
    """Returns the customer's current account balance. Requires authentication."""
    if not ctx.deps.is_authenticated:
        raise ModelRetry(
            "Authentication required. User must log in to access balance information."
        )
    
    balance = await ctx.deps.db.customer_balance(
        id=ctx.deps.customer_id,
        include_pending=include_pending,
    )    
    return f'${balance:.2f}'

@support_agent.tool
async def check_account_status(ctx: RunContext[SupportDependencies]) -> str:
    """Check if customer account is active. Requires authentication."""
    if not ctx.deps.is_authenticated:
        raise ModelRetry(
            "Authentication required. User must log in to check account status."
        )
    
    is_active = await ctx.deps.db.is_customer_active(id=ctx.deps.customer_id)
    return f"Account status: {'Active' if is_active else 'Inactive'}"

async def authenticate_and_create_deps(
    username: str, 
    password: str
) -> SupportDependencies:
    """Authenticate user and create dependencies object."""
    session_token = await auth_service.login(username, password)
    if not session_token:
        raise AuthenticationError("Invalid username or password")
    
    customer_id = await auth_service.validate_session(session_token)
    if not customer_id:
        raise AuthenticationError("Session validation failed")
    
    return SupportDependencies(
        customer_id=customer_id,
        db=DatabaseConn(),
        session_token=session_token,
        is_authenticated=True
    )

def create_unauthenticated_deps() -> SupportDependencies:
    """Create dependencies for unauthenticated user."""
    return SupportDependencies(
        customer_id=0,  # No valid customer ID
        db=DatabaseConn(),
        session_token=None,
        is_authenticated=False
    )

async def main():
    """Demonstrate the enhanced banking support agent with authentication."""
    
    print("=== Banking Support Agent Demo ===\n")
    
    # Test 1: Unauthenticated user trying to access account info
    print("Test 1: Unauthenticated user asking for balance")
    print("-" * 50)
    deps_unauth = create_unauthenticated_deps()
    user_prompt = "What is my account balance?"
    print(f'User (not logged in): {user_prompt}')
    
    try:
        result = await support_agent.run(user_prompt, deps=deps_unauth)
        print(f'Agent: {result.output.support_advice}')
        print(f'Risk Level: {result.output.risk}')
        print(f'Requires Auth: {result.output.requires_authentication}')
    except Exception as e:
        print(f'Error: {e}')
    
    print("\n" + "="*60 + "\n")
    
    # Test 2: Successful authentication and account query
    print("Test 2: User logs in and asks for balance")
    print("-" * 50)
    try:
        # Authenticate user
        deps_auth = await authenticate_and_create_deps('john_doe', 'password123')
        print('User: Successfully logged in as john_doe')
        
        user_prompt = "What is my current balance including pending transactions?"
        print(f'User (authenticated): {user_prompt}')
        
        result = await support_agent.run(user_prompt, deps=deps_auth)
        print(f'Agent: {result.output.support_advice}')
        print(f'Risk Level: {result.output.risk}')
        print(f'Block Card: {result.output.block_card}')
        
    except AuthenticationError as e:
        print(f'Authentication failed: {e}')
    except Exception as e:
        print(f'Error: {e}')
    
    print("\n" + "="*60 + "\n")
    
    # Test 3: Authenticated user with security concern
    print("Test 3: Authenticated user reports lost card")
    print("-" * 50)
    try:
        deps_auth = await authenticate_and_create_deps('jane_smith', 'securepass456')
        print('User: Successfully logged in as jane_smith')
        
        user_prompt = "I just lost my card and I'm worried about unauthorized transactions!"
        print(f'User (authenticated): {user_prompt}')
        
        result = await support_agent.run(user_prompt, deps=deps_auth)
        print(f'Agent: {result.output.support_advice}')
        print(f'Risk Level: {result.output.risk}')
        print(f'Block Card: {result.output.block_card}')
        
    except AuthenticationError as e:
        print(f'Authentication failed: {e}')
    except Exception as e:
        print(f'Error: {e}')
    
    print("\n" + "="*60 + "\n")
    
    # Test 4: Failed authentication
    print("Test 4: Failed login attempt")
    print("-" * 50)
    try:
        deps_auth = await authenticate_and_create_deps('john_doe', 'wrong_password')
    except AuthenticationError as e:
        print(f'Authentication failed: {e}')
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())