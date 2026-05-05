"""
Test suite for CPU Specialist Agent
Tests the LangGraph workflow and analysis capabilities
"""

import unittest
from unittest.mock import Mock, patch
import json
from cpu_agent import CPUSpecialistAgent, CPUAnalysisState
from datetime import datetime


class TestCPUSpecialistAgent(unittest.TestCase):
    """Test cases for CPU Specialist Agent"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_cpu_metrics = {
            "overall_cpu": 85.5,
            "process_cpu": 78.2,
            "system_cpu": 15.3,
            "user_cpu": 70.2,
            "thread_count": 150,
            "runnable_threads": 45,
            "blocked_threads": 12,
            "waiting_threads": 93,
            "cpu_cores": 8,
            "load_average": [6.5, 5.8, 5.2],
            "timestamp": datetime.now().isoformat()
        }
        
        self.sample_thread_dump = {
            "threads": [
                {"id": 1, "name": "http-nio-8080-exec-1", "state": "RUNNABLE", "cpu_time": 5000},
                {"id": 2, "name": "http-nio-8080-exec-2", "state": "RUNNABLE", "cpu_time": 4500},
                {"id": 3, "name": "pool-1-thread-1", "state": "BLOCKED", "cpu_time": 100},
                {"id": 4, "name": "pool-1-thread-2", "state": "WAITING", "cpu_time": 50},
                {"id": 5, "name": "pool-2-thread-1", "state": "RUNNABLE", "cpu_time": 3000}
            ]
        }
        
        self.high_cpu_metrics = {
            "overall_cpu": 98.5,
            "process_cpu": 95.2,
            "thread_count": 200,
            "runnable_threads": 150,
            "blocked_threads": 30,
            "cpu_cores": 8,
            "timestamp": datetime.now().isoformat()
        }
    
    def test_agent_initialization(self):
        """Test agent initialization"""
        agent = CPUSpecialistAgent(model_name="gpt-4", temperature=0.1)
        self.assertIsNotNone(agent)
        self.assertIsNotNone(agent.llm)
        self.assertIsNotNone(agent.workflow)
    
    def test_structure_cpu_metrics(self):
        """Test CPU metrics structuring"""
        agent = CPUSpecialistAgent()
        structured = agent._structure_cpu_metrics(self.sample_cpu_metrics)
        
        # Verify structure
        self.assertIn('overall_cpu_percent', structured)
        self.assertIn('process_cpu_percent', structured)
        self.assertIn('thread_count', structured)
        self.assertIn('cpu_per_core', structured)
        self.assertIn('runnable_ratio', structured)
        
        # Verify calculations
        self.assertEqual(structured['overall_cpu_percent'], 85.5)
        self.assertAlmostEqual(structured['cpu_per_core'], 85.5 / 8, places=2)
        self.assertAlmostEqual(structured['runnable_ratio'], 45 / 150, places=2)
    
    def test_collect_cpu_metrics_node(self):
        """Test the collect_cpu_metrics workflow node"""
        agent = CPUSpecialistAgent()
        
        initial_state = CPUAnalysisState(
            cpu_metrics=self.sample_cpu_metrics,
            thread_dump={},
            correlation_data={},
            cpu_hotspots=[],
            optimization_suggestions=[],
            analysis_summary="",
            errors=[]
        )
        
        result_state = agent.collect_cpu_metrics(initial_state)
        
        # Verify metrics were structured
        self.assertIsNotNone(result_state['cpu_metrics'])
        self.assertIn('overall_cpu_percent', result_state['cpu_metrics'])
        self.assertEqual(len(result_state['errors']), 0)
    
    def test_collect_cpu_metrics_empty_input(self):
        """Test collect_cpu_metrics with empty input"""
        agent = CPUSpecialistAgent()
        
        initial_state = CPUAnalysisState(
            cpu_metrics={},
            thread_dump={},
            correlation_data={},
            cpu_hotspots=[],
            optimization_suggestions=[],
            analysis_summary="",
            errors=[]
        )
        
        result_state = agent.collect_cpu_metrics(initial_state)
        
        # Should have an error
        self.assertGreater(len(result_state['errors']), 0)
        self.assertIn("No CPU metrics provided", result_state['errors'][0])
    
    def test_summarize_thread_dump(self):
        """Test thread dump summarization"""
        agent = CPUSpecialistAgent()
        summary = agent._summarize_thread_dump(self.sample_thread_dump)
        
        # Verify summary structure
        self.assertIn('total_threads', summary)
        self.assertIn('thread_states', summary)
        self.assertIn('top_cpu_threads', summary)
        self.assertIn('blocked_threads', summary)
        
        # Verify counts
        self.assertEqual(summary['total_threads'], 5)
        self.assertEqual(summary['thread_states']['RUNNABLE'], 3)
        self.assertEqual(summary['thread_states']['BLOCKED'], 1)
        self.assertEqual(len(summary['blocked_threads']), 1)
        
        # Verify top CPU threads are sorted
        self.assertGreater(len(summary['top_cpu_threads']), 0)
        if len(summary['top_cpu_threads']) > 1:
            self.assertGreaterEqual(
                summary['top_cpu_threads'][0]['cpu_time'],
                summary['top_cpu_threads'][1]['cpu_time']
            )
    
    def test_prepare_correlation_data(self):
        """Test correlation data preparation"""
        agent = CPUSpecialistAgent()
        structured_metrics = agent._structure_cpu_metrics(self.sample_cpu_metrics)
        
        correlation_data = agent._prepare_correlation_data(
            structured_metrics,
            self.sample_thread_dump
        )
        
        # Verify structure
        self.assertIn('cpu_snapshot', correlation_data)
        self.assertIn('thread_snapshot', correlation_data)
        self.assertIn('timing', correlation_data)
        
        # Verify content
        self.assertEqual(correlation_data['cpu_snapshot']['overall_cpu'], 85.5)
        self.assertEqual(correlation_data['thread_snapshot']['total_threads'], 5)
    
    @patch('cpu_agent.ChatOpenAI')
    def test_correlate_with_threads_node(self, mock_llm):
        """Test the correlate_with_threads workflow node"""
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = json.dumps({
            'cpu_intensive_threads': [
                {'name': 'http-nio-8080-exec-1', 'cpu_percentage': 25.5}
            ],
            'spike_patterns': 'CPU spikes during request processing',
            'thread_states_analysis': 'High runnable thread count',
            'contention_indicators': 'Blocked threads detected',
            'timing_correlation': 'CPU correlates with HTTP requests'
        })
        mock_llm.return_value.invoke.return_value = mock_response
        
        agent = CPUSpecialistAgent()
        agent.llm = mock_llm.return_value
        
        state = CPUAnalysisState(
            cpu_metrics=agent._structure_cpu_metrics(self.sample_cpu_metrics),
            thread_dump=self.sample_thread_dump,
            correlation_data={},
            cpu_hotspots=[],
            optimization_suggestions=[],
            analysis_summary="",
            errors=[]
        )
        
        result_state = agent.correlate_with_threads(state)
        
        # Verify correlation was performed
        self.assertIsNotNone(result_state['correlation_data'])
        self.assertGreater(len(result_state['correlation_data']), 0)
    
    @patch('cpu_agent.ChatOpenAI')
    def test_identify_hotspots_node(self, mock_llm):
        """Test the identify_hotspots workflow node"""
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = json.dumps([
            {
                'type': 'Inefficient Algorithm',
                'severity': 'High',
                'threads': ['http-nio-8080-exec-1'],
                'cpu_impact': 45.2,
                'root_cause': 'O(n²) complexity in data processing',
                'performance_impact': 'Response time degradation'
            }
        ])
        mock_llm.return_value.invoke.return_value = mock_response
        
        agent = CPUSpecialistAgent()
        agent.llm = mock_llm.return_value
        
        state = CPUAnalysisState(
            cpu_metrics=agent._structure_cpu_metrics(self.sample_cpu_metrics),
            thread_dump=self.sample_thread_dump,
            correlation_data={'cpu_intensive_threads': []},
            cpu_hotspots=[],
            optimization_suggestions=[],
            analysis_summary="",
            errors=[]
        )
        
        result_state = agent.identify_hotspots(state)
        
        # Verify hotspots were identified
        self.assertIsNotNone(result_state['cpu_hotspots'])
        self.assertGreater(len(result_state['cpu_hotspots']), 0)
    
    @patch('cpu_agent.ChatOpenAI')
    def test_suggest_optimizations_node(self, mock_llm):
        """Test the suggest_optimizations workflow node"""
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = json.dumps({
            'optimizations': [
                {
                    'type': 'Algorithm Optimization',
                    'target': 'DataProcessor.process()',
                    'recommended_solution': 'Use HashMap for O(n) lookup',
                    'expected_cpu_reduction': 40,
                    'priority': 'High'
                }
            ],
            'thread_pool_tuning': {
                'current_size': 50,
                'recommended_size': 100
            },
            'jvm_flags': ['-XX:+UseParallelGC'],
            'summary': 'Optimization recommendations generated'
        })
        mock_llm.return_value.invoke.return_value = mock_response
        
        agent = CPUSpecialistAgent()
        agent.llm = mock_llm.return_value
        
        state = CPUAnalysisState(
            cpu_metrics=agent._structure_cpu_metrics(self.high_cpu_metrics),
            thread_dump=self.sample_thread_dump,
            correlation_data={'cpu_intensive_threads': []},
            cpu_hotspots=[{'type': 'Inefficient Algorithm', 'severity': 'High'}],
            optimization_suggestions=[],
            analysis_summary="",
            errors=[]
        )
        
        result_state = agent.suggest_optimizations(state)
        
        # Verify suggestions were generated
        self.assertIsNotNone(result_state['optimization_suggestions'])
        self.assertIsNotNone(result_state['analysis_summary'])
    
    def test_generate_summary(self):
        """Test summary generation"""
        agent = CPUSpecialistAgent()
        
        state = CPUAnalysisState(
            cpu_metrics=agent._structure_cpu_metrics(self.sample_cpu_metrics),
            thread_dump={},
            correlation_data={},
            cpu_hotspots=[
                {'type': 'Busy Loop', 'severity': 'Critical'},
                {'type': 'Lock Contention', 'severity': 'High'}
            ],
            optimization_suggestions={'optimizations': []},
            analysis_summary="",
            errors=[]
        )
        
        summary = agent._generate_summary(state)
        
        # Verify summary content
        self.assertIn('CPU Analysis Summary', summary)
        self.assertIn('Overall CPU: 85.5%', summary)
        self.assertIn('Hotspots Identified: 2', summary)
        self.assertIn('Critical', summary)
    
    def test_workflow_structure(self):
        """Test that workflow has correct structure"""
        agent = CPUSpecialistAgent()
        
        # Verify workflow exists
        self.assertIsNotNone(agent.workflow)
        
        # Workflow should be compiled
        self.assertTrue(hasattr(agent.workflow, 'invoke'))
    
    def test_high_cpu_detection(self):
        """Test detection of high CPU scenarios"""
        agent = CPUSpecialistAgent()
        structured = agent._structure_cpu_metrics(self.high_cpu_metrics)
        
        # Verify high CPU is captured
        self.assertGreater(structured['overall_cpu_percent'], 90)
        self.assertGreater(structured['runnable_ratio'], 0.5)
    
    def test_thread_state_analysis(self):
        """Test thread state analysis"""
        agent = CPUSpecialistAgent()
        summary = agent._summarize_thread_dump(self.sample_thread_dump)
        
        # Verify thread states are counted
        total_states = sum(summary['thread_states'].values())
        self.assertEqual(total_states, 5)
        
        # Verify blocked threads are identified
        self.assertEqual(len(summary['blocked_threads']), 1)
        self.assertEqual(summary['blocked_threads'][0]['name'], 'pool-1-thread-1')


class TestCPUMetricsStructuring(unittest.TestCase):
    """Test cases for CPU metrics structuring"""
    
    def test_derived_metrics_calculation(self):
        """Test calculation of derived metrics"""
        agent = CPUSpecialistAgent()
        
        metrics = {
            "overall_cpu": 80.0,
            "cpu_cores": 4,
            "thread_count": 100,
            "runnable_threads": 30,
            "blocked_threads": 10
        }
        
        structured = agent._structure_cpu_metrics(metrics)
        
        # Verify derived metrics
        self.assertEqual(structured['cpu_per_core'], 20.0)
        self.assertEqual(structured['runnable_ratio'], 0.3)
        self.assertEqual(structured['blocked_ratio'], 0.1)
    
    def test_missing_optional_fields(self):
        """Test handling of missing optional fields"""
        agent = CPUSpecialistAgent()
        
        minimal_metrics = {
            "overall_cpu": 50.0
        }
        
        structured = agent._structure_cpu_metrics(minimal_metrics)
        
        # Should have defaults
        self.assertEqual(structured['overall_cpu_percent'], 50.0)
        self.assertEqual(structured['thread_count'], 0)
        self.assertEqual(structured['cpu_cores'], 1)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)

# Made with Bob
