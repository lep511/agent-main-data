import asyncio
from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.tools import google_search
from google.adk.runners import InMemoryRunner
from google.adk.sessions import InMemorySessionService
from google.genai import types

def create_company_detective_agent():
    """
    Creates a comprehensive company research agent system using Google ADK for Python.
    This system performs parallel market research and compiles a final report.
    """
    
    # Individual research agents
    company_profiler = LlmAgent(
        name="company_profiler",  # Changed from "company-profiler"
        description="Provides a general overview of a company.",
        instruction="""
        Your role is to provide a brief overview of the
        given company.
        Include its mission, headquarters, and current CEO.
        Use the Google Search Tool to find this information.
        """,
        model="gemini-2.5-flash",
        tools=[google_search],
        output_key="profile"
    )

    news_finder = LlmAgent(
        name="news_finder",  # Changed from "news-finder"
        description="Finds the latest news about a company.",
        instruction="""
        Your role is to find the top 3-4 recent news headlines
        for the given company.
        Use the Google Search Tool.
        Present the results as a simple bulleted list.
        """,
        model="gemini-2.5-flash",
        tools=[google_search],
        output_key="news"
    )

    financial_analyst = LlmAgent(
        name="financial_analyst",  # Changed from "financial-analyst"
        description="Analyzes the financial performance of a company.",
        instruction="""
        Your role is to provide a snapshot of the given company's
        recent financial performance.
        Focus on stock trends or recent earnings reports.
        Use the Google Search Tool.
        """,
        model="gemini-2.5-flash",
        tools=[google_search],
        output_key="financials"
    )

    # Parallel agent to coordinate research
    market_researcher = ParallelAgent(
        name="market_researcher",  # Changed from "market-researcher"
        description="Performs comprehensive market research on a company.",
        sub_agents=[
            company_profiler,
            news_finder,
            financial_analyst
        ]
    )

    # Report compilation agent
    report_compiler = LlmAgent(
        name="report_compiler",  # Changed from "report-compiler"
        description="Compiles a final market research report.",
        instruction="""
        Your role is to synthesize the provided information
        into a coherent market research report.
        Combine the company profile, latest news, and
        financial analysis into a single, well-formatted report.

        ## Company Profile
        {profile}

        ## Latest News
        {news}

        ## Financial Snapshot
        {financials}
        """,
        model="gemini-2.5-flash"
    )

    # Main sequential agent
    company_detective = SequentialAgent(
        name="company_detective",  # Changed from "company-detective"
        description="Collects various market information about a company.",
        sub_agents=[
            market_researcher,
            report_compiler
        ]
    )

    return company_detective

async def main():
    """
    Main async function to demonstrate usage of the company detective agent.
    """
    # Create the agent system
    detective_agent = create_company_detective_agent()
    
    # Create InMemoryRunner with just the agent
    runner = InMemoryRunner(detective_agent)
    
    # Create a session using the runner's session service with named parameters
    app_name = "CompanyDetective"
    user_id = "test_user_123"
    session = await runner.session_service.create_session(
        app_name=app_name,
        user_id=user_id
    )
    
    # Create user message
    user_message = types.Content(parts=[types.Part(text="Research Tesla Inc.")])
    
    try:
        print("Starting company research...")
        
        invocation_context = InvocationContext(
            user_id=user_id,
            session_id=session.id,
            message=user_message
        )
        # Execute the agent using the runner
        event_stream = runner.run_async(invocation_context)
        
        print("=== Company Research Report ===")
        
        # Process the event stream
        async for event in event_stream:
            if hasattr(event, 'content') and event.content:
                # Print the content of each event
                if hasattr(event.content, 'parts'):
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            print(part.text)
            
            # Check if this is the final response
            if hasattr(event, 'is_final_response') and event.is_final_response():
                print("\n--- Research Complete ---")
                
    except Exception as e:
        print(f"Error during research: {e}")
        import traceback
        traceback.print_exc()

# Usage example
if __name__ == "__main__":
    # Create the agent system
    detective_agent = create_company_detective_agent()
    
    # Run the async main function
    asyncio.run(main())
    
    # Alternative: For Jupyter notebooks or environments with existing event loop
    # await main()