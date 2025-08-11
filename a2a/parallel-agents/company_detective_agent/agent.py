from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent
from google.adk.tools import google_search

GEMINI_MODEL = "gemini-2.5-flash"
   
# Individual research agents
company_profiler = LlmAgent(
    name="CompanyProfiler",
    description="Provides a general overview of a company.",
    instruction="""
    Your role is to provide a brief overview of the given company.
    Include its mission, headquarters, and current CEO.
    Use the Google Search Tool to find this information.
    """,
    model=GEMINI_MODEL,
    tools=[google_search],
    output_key="profile"
)

news_finder = LlmAgent(
    name="NewsFinder", 
    description="Finds the latest news about a company.",
    instruction="""
    Your role is to find the top 3-4 recent news headlines for the given company.
    Use the Google Search Tool.
    Present the results as a simple bulleted list.
    """,
    model=GEMINI_MODEL,
    tools=[google_search],
    output_key="news"
)

financial_analyst = LlmAgent(
    name="FinancialAnalyst", 
    description="Analyzes the financial performance of a company.",
    instruction="""
    Your role is to provide a snapshot of the given company's recent financial performance.
    Focus on stock trends or recent earnings reports.
    Use the Google Search Tool.
    """,
    model=GEMINI_MODEL,
    tools=[google_search],
    output_key="financials"
)

# Parallel agent to coordinate research
market_researcher = ParallelAgent(
    name="MarketResearcher",
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
    Your role is to synthesize the provided information into a coherent market research report.
    Combine the company profile, latest news, and financial analysis into a single, well-formatted report.

    ## Company Profile
    {profile}

    ## Latest News
    {news}

    ## Financial Snapshot
    {financials}
    """,
    model=GEMINI_MODEL
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

root_agent = company_detective