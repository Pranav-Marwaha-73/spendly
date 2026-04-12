<h1>🚀 Self-Correcting Multi-Agent AI Research System</h1>

<p>
A powerful multi-agent AI system that refines queries, performs deep research, and improves responses in real-time using a <b>CRAG (Corrective RAG)</b> architecture.
</p>

<hr>

<h2>🧠 Overview</h2>

<p>This project goes beyond traditional chatbots by combining:</p>

<p>
• Multi-agent orchestration <br>
• Self-correcting retrieval pipelines <br>
• Deep research capabilities <br>
• Persistent + short-term memory
</p>

<p>
👉 The system continuously improves its responses by refining retrieved information and leveraging multiple agents.
</p>

<hr>

<h2>⚙️ Features</h2>

<p>
💬 Chat interface with persistent memory (Supabase) <br>
🧠 Short-term memory summarization (after every 6 conversations) <br>
🔁 CRAG-based query refinement pipeline <br>
🔍 Deep Research Agent with parallel execution <br>
🛠️ Tool integrations: <br>
&nbsp;&nbsp;&nbsp;&nbsp;• Web Search <br>
&nbsp;&nbsp;&nbsp;&nbsp;• Calculator <br>
&nbsp;&nbsp;&nbsp;&nbsp;• Stock Data <br>
&nbsp;&nbsp;&nbsp;&nbsp;• Currency Converter <br>
&nbsp;&nbsp;&nbsp;&nbsp;• Weather API <br>
🖼️ Image generation during research workflows <br>
🔌 MCP (Model Context Protocol) integration <br>
⚡ Async execution for high performance
</p>

<hr>

<h2>🧩 System Components</h2>

<h3>1. ReAct Agent</h3>
<p>
Handles user interaction <br>
Performs reasoning + tool usage <br>
Maintains conversation flow
</p>

<h3>2. CRAG Pipeline (Core Innovation)</h3>

<p><b>Flow:</b><br>
Retrieve → Evaluate → Rewrite → Search → Merge → Generate
</p>

<p>
👉 Ensures: <br>
• Better context <br>
• Improved responses <br>
• Reduced irrelevant outputs
</p>

<h3>3. Deep Research Agent</h3>
<p>
Planner + worker architecture <br>
Parallel execution <br>
Multi-step reasoning <br>
Image generation support
</p>

<h3>4. Memory System</h3>
<p>
Long-term memory: Supabase (PostgreSQL) <br>
Short-term memory: summarization node <br>
Vector storage: FAISS
</p>

<hr>

<h2>🛠️ Tech Stack</h2>

<p>
Frontend: Streamlit <br>
Backend: Python <br>
Framework: LangGraph / LangChain <br>
LLM: OpenAI (GPT-4o-mini) <br>
Search: Tavily API <br>
Database: Supabase (PostgreSQL) <br>
Vector Store: FAISS <br>
Image Generation: Gemini API <br>
Observability: LangSmith
</p>

<hr>

<h2>🚀 Getting Started</h2>

<h3>1. Clone the repo</h3>
<pre>
git clone https://github.com/your-username/your-repo.git
cd your-repo
</pre>

<h3>2. Create virtual environment</h3>
<pre>
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
</pre>

<h3>3. Install dependencies</h3>
<pre>
pip install -r requirements.txt
</pre>

<h3>4. Setup environment variables</h3>

<p>Create a <b>.env</b> file:</p>

<pre>
OPENAI_API_KEY=your_key
TAVILY_API_KEY=your_key
SUPABASE_URL=your_url
SUPABASE_KEY=your_key
GEMINI_API_KEY=your_key
</pre>

<h3>5. Run the app</h3>
<pre>
streamlit run ReAct_Agent.py
</pre>

<hr>

<h2>⚔️ Challenges</h2>

<p>
Running multi-agent workflows on limited resources (Render free tier) <br>
Managing async execution and parallelism <br>
Optimizing CRAG pipeline for low API cost <br>
Secure API handling using in-memory (zero-trust approach)
</p>

<hr>

<h2>🏆 Achievements</h2>

<p>
Built a complete multi-agent AI system <br>
Implemented CRAG with dynamic query refinement <br>
Integrated chat + research agents <br>
Successfully deployed under constraints
</p>

<hr>

<h2>📚 Learnings</h2>

<p>
Multi-agent system design (LangGraph) <br>
State and memory management <br>
Async and parallel workflows <br>
Advanced RAG pipelines with subgraphs
</p>

<hr>

<h2>🔮 Future Work</h2>

<p>
🧠 Universal Brain Agent <br>
🔐 Secure sandboxed code execution <br>
🤖 Autonomous project-building agents <br>
📈 Scaling multi-agent orchestration
</p>

<hr>

<h2>🤝 Contributing</h2>

<p>
Pull requests are welcome. For major changes, please open an issue first.
</p>

<hr>

<h2>📜 License</h2>

<p>MIT License</p>

<hr>

<h2>⭐ If you like this project, give it a star!</h2>
