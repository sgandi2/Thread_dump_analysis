"""
AI-Powered Recommendation Generator using Ollama
Analyzes thread dumps and provides intelligent code-level recommendations
"""
import json
import requests
from typing import List, Dict, Any
from pathlib import Path


def generate_ai_recommendations(threads_info: List[Dict], root_cause: str, issue_type: str) -> List[str]:
    """
    Generate AI-powered recommendations using Ollama
    
    Args:
        threads_info: List of thread information dictionaries
        root_cause: Root cause analysis string
        issue_type: Type of issue (hung, long_running, blocked)
    
    Returns:
        List of AI-generated recommendations
    """
    try:
        # Prepare context for AI
        context = f"""You are an expert Java performance analyst. Analyze this thread dump issue and provide specific, actionable recommendations.

Issue Type: {issue_type}
Root Cause: {root_cause}

Affected Threads:
"""
        for thread in threads_info[:3]:  # Top 3 threads
            context += f"\nThread: {thread['name']}\n"
            context += f"State: {thread['state']}\n"
            context += f"CPU Time: {thread['cpu_time']}s\n"
            if thread.get('stack_trace'):
                context += f"Stack Trace (top 5 lines):\n"
                for line in thread['stack_trace'][:5]:
                    context += f"  {line}\n"
            context += "\n"
        
        context += """
Provide 5-6 specific recommendations in this format:
1. Immediate Action: [What to do right now]
2. Code Fix: [What code changes are needed and where]
3. Configuration: [Any configuration changes needed]
4. Prevention: [How to prevent this in future]
5. Monitoring: [What to monitor going forward]
6. Recovery: [Include restarting webMethods Integration Server as a recovery option]

Be specific about:
- Exact methods/classes to review
- Specific code patterns causing the issue
- Configuration parameters to adjust
- Tools or techniques to use
- When to restart the Integration Server

Keep each recommendation concise (1-2 sentences).
"""
        
        # Call Ollama API
        ollama_url = "http://localhost:11434/api/generate"
        
        payload = {
            "model": "llama2",  # or "codellama", "mistral", etc.
            "prompt": context,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 500
            }
        }
        
        print("🤖 Generating AI recommendations with Ollama...")
        response = requests.post(ollama_url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result.get('response', '')
            
            # Parse recommendations
            recommendations = []
            lines = ai_response.strip().split('\n')
            current_rec = ""
            
            for line in lines:
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                    if current_rec:
                        recommendations.append(current_rec.strip())
                    current_rec = line
                elif line and current_rec:
                    current_rec += " " + line
            
            if current_rec:
                recommendations.append(current_rec.strip())
            
            # If parsing failed, split by sentences
            if not recommendations:
                recommendations = [s.strip() + '.' for s in ai_response.split('.') if s.strip()][:5]
            
            print(f"✅ Generated {len(recommendations)} AI recommendations")
            return recommendations[:5]  # Return top 5
        
        else:
            print(f"⚠️  Ollama API error: {response.status_code}")
            return get_fallback_recommendations(issue_type, root_cause)
    
    except requests.exceptions.ConnectionError:
        print("⚠️  Ollama not running. Start with: ollama serve")
        return get_fallback_recommendations(issue_type, root_cause)
    
    except Exception as e:
        print(f"⚠️  AI recommendation error: {e}")
        return get_fallback_recommendations(issue_type, root_cause)


def get_fallback_recommendations(issue_type: str, root_cause: str) -> List[str]:
    """Fallback recommendations when AI is not available"""
    
    base_recs = {
        "hung": [
            "Immediate: Kill hung threads using Integration Server Admin Console > Thread Management",
            "Code Fix: Review and add timeout parameters to long-running operations",
            "Configuration: Increase thread timeout threshold in server.cnf",
            "Prevention: Implement circuit breakers for external service calls",
            "Monitoring: Set up alerts for threads exceeding 30s CPU time",
            "Recovery: Restart webMethods Integration Server to clear all hung threads"
        ],
        "long_running": [
            "Immediate: Monitor these threads - they may become hung soon",
            "Code Fix: Optimize the identified operations (check for inefficient queries/loops)",
            "Configuration: Review and tune connection pool sizes",
            "Prevention: Add performance profiling to identify bottlenecks",
            "Monitoring: Track thread execution times in application logs",
            "Recovery: If threads become hung, restart webMethods Integration Server"
        ],
        "blocked": [
            "Immediate: Identify lock holders and review their operations",
            "Code Fix: Reduce synchronized block scope or use concurrent collections",
            "Configuration: Review database connection pool settings",
            "Prevention: Implement lock-free algorithms where possible",
            "Monitoring: Enable deadlock detection and logging",
            "Recovery: Restart webMethods Integration Server to release all locks"
        ]
    }
    
    recs = base_recs.get(issue_type, base_recs["long_running"])
    
    # Customize based on root cause
    if "database" in root_cause.lower():
        recs[1] = "Code Fix: Optimize database queries - add indexes, reduce joins, use pagination"
        recs[2] = "Configuration: Increase database connection pool size and timeout"
    elif "network" in root_cause.lower():
        recs[1] = "Code Fix: Add connection timeouts and retry logic with exponential backoff"
        recs[2] = "Configuration: Tune socket timeout and keep-alive settings"
    elif "lock" in root_cause.lower():
        recs[1] = "Code Fix: Refactor to use ReadWriteLock or reduce lock contention"
        recs[2] = "Configuration: Enable JVM lock contention monitoring (-XX:+PrintConcurrentLocks)"
    
    return recs


if __name__ == "__main__":
    # Test the AI recommendation generator
    test_threads = [
        {
            "name": "pool-1-thread-1",
            "state": "RUNNABLE",
            "cpu_time": 65.5,
            "stack_trace": [
                "com.wm.app.b2b.server.ServiceManager.invoke(ServiceManager.java:123)",
                "com.wm.app.b2b.server.BaseService.baseInvoke(BaseService.java:456)",
                "java.sql.Statement.executeQuery(Statement.java:789)"
            ]
        }
    ]
    
    root_cause = "1 thread(s) blocked on database operations. Database operation in pool-1-thread-1: com.wm.app.b2b.server.ServiceManager.invoke"
    
    recommendations = generate_ai_recommendations(test_threads, root_cause, "hung")
    
    print("\n📋 AI Recommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")

# Made with Bob
