# MCP Toolbox for Databases

## Overview

MCP Toolbox for Databases is an open source MCP server for databases. It enables you to develop tools easier, faster, and more securely by handling the complexities such as connection pooling, authentication, and more.

Originally developed as "Gen AI Toolbox for Databases," this project has been renamed to align with the Model Context Protocol (MCP) standard, providing a powerful bridge between AI applications and database systems.

## ⚠️ Beta Notice

MCP Toolbox for Databases is currently in beta, and may see breaking changes until the first stable release (v1.0).

## Why Use Toolbox?

### Key Benefits

Toolbox helps you build Gen AI tools that let your agents access data in your database. Toolbox provides:
- Simplified development: Integrate tools to your agent in less than 10 lines of code, reuse tools between multiple agents or frameworks, and deploy new versions of tools more easily.
- Better performance: Best practices such as connection pooling, authentication, and more.
- Enhanced security: Integrated auth for more secure access to your data
- End-to-end observability: Out of the box metrics and tracing with built-in support for OpenTelemetry.

### Architecture

Toolbox sits between your application's orchestration framework and your database, providing a control plane that is used to modify, distribute, or invoke tools. It simplifies the management of your tools by providing you with a centralized location to store and update tools, allowing you to share tools between agents and applications and update those tools without necessarily redeploying your application.

## Installation

### Binary Installation

```bash
# Check releases page for latest version
export VERSION=0.8.0
curl -O https://storage.googleapis.com/genai-toolbox/v$VERSION/linux/amd64/toolbox
chmod +x toolbox
```

### Container Installation

```bash
# Check releases page for latest version
export VERSION=0.8.0
docker pull us-central1-docker.pkg.dev/database-toolbox/toolbox/toolbox:$VERSION
```

### Build from Source

Ensure you have Go installed, then:

```bash
go install github.com/googleapis/genai-toolbox@v0.8.0
```

## Quick Start

### 1. Configure Your Tools

Create a `tools.yaml` file to define your data sources, tools, and toolsets:

```yaml
# Data sources configuration
sources:
  my-postgres-db:
    kind: postgres
    host: 127.0.0.1
    port: 5432
    database: my_database
    user: my_user
    password: my_password

# Tool definitions
tools:
  search-users:
    kind: postgres-sql
    source: my-postgres-db
    description: Search for users by name
    parameters:
      - name: name
        type: string
        description: The name to search for
    statement: SELECT * FROM users WHERE name ILIKE '%' || $1 || '%'

  get-user-orders:
    kind: postgres-sql
    source: my-postgres-db
    description: Get orders for a specific user
    parameters:
      - name: user_id
        type: integer
        description: The user ID
    statement: SELECT * FROM orders WHERE user_id = $1

# Toolset groupings
toolsets:
  user-management:
    - search-users
    - get-user-orders
```

### 2. Start the Server

```bash
./toolbox --tools-file "tools.yaml"
```

### 3. Integrate with Your Application

Choose your preferred framework:

#### Core SDK
```bash
pip install toolbox-core
```

```python
from toolbox_core import ToolboxClient

client = ToolboxClient("http://127.0.0.1:5000")
tools = await client.load_toolset("user-management")
```

#### LangChain/LangGraph
```bash
pip install toolbox-langchain
```

```python
from toolbox_langchain import ToolboxClient

client = ToolboxClient("http://127.0.0.1:5000")
tools = client.load_toolset("user-management")
```

#### LlamaIndex
```bash
pip install toolbox-llamaindex
```

```python
from toolbox_llamaindex import ToolboxClient

client = ToolboxClient("http://127.0.0.1:5000")
tools = client.load_toolset("user-management")
```

## Configuration

### Supported Data Sources

- **PostgreSQL**: Full-featured SQL database support
- **MySQL**: Comprehensive MySQL integration
- **SQLite**: Lightweight database support
- **BigQuery**: Google Cloud data warehouse
- **Cloud SQL**: Google Cloud managed databases

### Tool Types

- **SQL Tools**: Execute parameterized SQL queries
- **Stored Procedures**: Call database stored procedures
- **Custom Functions**: Execute custom database functions

### Security Features

- **Connection Pooling**: Efficient database connection management
- **Authentication**: Secure database access control
- **Parameter Validation**: SQL injection prevention
- **Access Control**: Role-based permissions

## Advanced Features

### Observability

Built-in support for:
- OpenTelemetry integration
- Metrics collection
- Distributed tracing
- Performance monitoring

### Deployment Options

- **Local Development**: Binary or source installation
- **Container Deployment**: Docker and Kubernetes support
- **Cloud Deployment**: Google Cloud, AWS, Azure compatible
- **CI/CD Integration**: Automated deployment pipelines

### Tool Management

- **Version Control**: Track tool changes over time
- **Hot Reloading**: Update tools without restart
- **Rollback Support**: Revert to previous tool versions
- **A/B Testing**: Deploy multiple tool versions

## Use Cases

### AI Agent Development
- Enable agents to query databases directly
- Provide real-time data access to language models
- Create dynamic, data-driven responses

### Enterprise Integration
- Connect AI systems to existing databases
- Standardize data access across AI applications
- Centralize tool management and governance

### RAG Applications
- Enhance retrieval with structured data
- Combine vector search with SQL queries
- Improve context with real-time information

### Business Intelligence
- AI-powered data exploration
- Natural language database queries
- Automated report generation

## Performance Optimizations

- **Connection Pooling**: Reuse database connections
- **Query Caching**: Cache frequently used queries
- **Prepared Statements**: Optimize SQL execution
- **Batching**: Execute multiple operations efficiently

## Security Best Practices

- **Parameterized Queries**: Prevent SQL injection
- **Access Control**: Limit database permissions
- **Audit Logging**: Track all database access
- **Encryption**: Secure data in transit and at rest

## Monitoring and Debugging

### Built-in Metrics
- Query execution time
- Connection pool utilization
- Error rates and types
- Tool usage statistics

### Debugging Tools
- Query logging and analysis
- Connection status monitoring
- Performance profiling
- Error tracking and alerting

## API Reference

### Core Client Methods
- `load_toolset(name)`: Load specific toolset
- `load_all_tools()`: Load all available tools
- `get_tool_schema(name)`: Get tool definition
- `execute_tool(name, params)`: Execute tool directly

### Configuration Options
- `--tools-file`: Specify tools configuration file
- `--port`: Set server port (default: 5000)
- `--host`: Set server host (default: 127.0.0.1)
- `--log-level`: Set logging level
- `--metrics-port`: Set metrics endpoint port

## Contributing

We welcome contributions! Please see our [Contributing Guide](https://github.com/googleapis/genai-toolbox/blob/main/CONTRIBUTING.md) for details.

### Development Setup
1. Clone the repository
2. Install Go dependencies
3. Run tests: `go test ./...`
4. Build: `go build`

### Code of Conduct
This project follows the [Contributor Code of Conduct](https://github.com/googleapis/genai-toolbox/blob/main/CODE_OF_CONDUCT.md).

## Versioning

This project uses [semantic versioning](https://semver.org/):
- **MAJOR**: Incompatible API changes
- **MINOR**: Backward-compatible functionality
- **PATCH**: Backward-compatible bug fixes

## Resources

- **Documentation**: [https://googleapis.github.io/genai-toolbox/](https://googleapis.github.io/genai-toolbox/)
- **GitHub Repository**: [https://github.com/googleapis/genai-toolbox](https://github.com/googleapis/genai-toolbox)
- **Releases**: [https://github.com/googleapis/genai-toolbox/releases](https://github.com/googleapis/genai-toolbox/releases)
- **Python SDK**: [https://pypi.org/project/toolbox-core/](https://pypi.org/project/toolbox-core/)

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](https://github.com/googleapis/genai-toolbox/blob/main/LICENSE) file for details.

## Support

For questions and support:
- Check the [FAQ](https://googleapis.github.io/genai-toolbox/about/faq/)
- Browse [How-to guides](https://googleapis.github.io/genai-toolbox/how-to/)
- Open an [issue](https://github.com/googleapis/genai-toolbox/issues) on GitHub

---
