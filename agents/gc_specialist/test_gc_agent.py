"""
Test suite for GC Specialist Agent
Tests the LangGraph workflow and analysis capabilities
"""

import unittest
from unittest.mock import Mock, patch
import json
from gc_agent import GCSpecialistAgent, GCAnalysisState


class TestGCSpecialistAgent(unittest.TestCase):
    """Test cases for GC Specialist Agent"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_gc_log = """
[GC (Allocation Failure) 2023-01-15T10:30:45.123+0000: 1024K->512K(2048K), 0.0234567 secs]
[GC (Allocation Failure) 2023-01-15T10:30:50.456+0000: 1536K->768K(2048K), 0.0345678 secs]
[Full GC (Ergonomics) 2023-01-15T10:31:00.789+0000: 1800K->600K(2048K), 1.2345678 secs]
[GC (Allocation Failure) 2023-01-15T10:31:10.012+0000: 1280K->640K(2048K), 0.0456789 secs]
[GC (Allocation Failure) 2023-01-15T10:31:15.345+0000: 1400K->700K(2048K), 0.0567890 secs]
[Full GC (System.gc()) 2023-01-15T10:31:30.678+0000: 1900K->650K(2048K), 1.3456789 secs]
"""
        
        self.problematic_gc_log = """
[GC (Allocation Failure) 2023-01-15T10:30:00.000+0000: 1800K->1700K(2048K), 0.5234567 secs]
[Full GC (Ergonomics) 2023-01-15T10:30:05.000+0000: 1950K->1850K(2048K), 2.5345678 secs]
[Full GC (Ergonomics) 2023-01-15T10:30:10.000+0000: 1980K->1900K(2048K), 2.7456789 secs]
[Full GC (Ergonomics) 2023-01-15T10:30:15.000+0000: 1990K->1950K(2048K), 3.1567890 secs]
[Full GC (Ergonomics) 2023-01-15T10:30:20.000+0000: 2000K->1980K(2048K), 3.5678901 secs]
"""
    
    def test_agent_initialization(self):
        """Test agent initialization"""
        agent = GCSpecialistAgent(model_name="gpt-4", temperature=0.1)
        self.assertIsNotNone(agent)
        self.assertIsNotNone(agent.llm)
        self.assertIsNotNone(agent.workflow)
    
    def test_parse_gc_logs(self):
        """Test GC log parsing"""
        agent = GCSpecialistAgent()
        metrics = agent._parse_gc_logs(self.sample_gc_log)
        
        # Verify metrics structure
        self.assertIn('young_gc_count', metrics)
        self.assertIn('full_gc_count', metrics)
        self.assertIn('total_pause_time', metrics)
        self.assertIn('max_pause_time', metrics)
        
        # Verify counts
        self.assertEqual(metrics['young_gc_count'], 4)  # 4 regular GCs
        self.assertEqual(metrics['full_gc_count'], 2)   # 2 Full GCs
        
        # Verify pause times are calculated
        self.assertGreater(metrics['total_pause_time'], 0)
        self.assertGreater(metrics['max_pause_time'], 0)
    
    def test_collect_gc_logs_node(self):
        """Test the collect_gc_logs workflow node"""
        agent = GCSpecialistAgent()
        
        initial_state = GCAnalysisState(
            gc_logs=self.sample_gc_log,
            raw_metrics={},
            gc_patterns={},
            memory_issues=[],
            tuning_recommendations=[],
            analysis_summary="",
            errors=[]
        )
        
        result_state = agent.collect_gc_logs(initial_state)
        
        # Verify metrics were extracted
        self.assertIsNotNone(result_state['raw_metrics'])
        self.assertGreater(len(result_state['raw_metrics']), 0)
        self.assertEqual(len(result_state['errors']), 0)
    
    def test_collect_gc_logs_empty_input(self):
        """Test collect_gc_logs with empty input"""
        agent = GCSpecialistAgent()
        
        initial_state = GCAnalysisState(
            gc_logs="",
            raw_metrics={},
            gc_patterns={},
            memory_issues=[],
            tuning_recommendations=[],
            analysis_summary="",
            errors=[]
        )
        
        result_state = agent.collect_gc_logs(initial_state)
        
        # Should have an error
        self.assertGreater(len(result_state['errors']), 0)
        self.assertIn("No GC logs provided", result_state['errors'][0])
    
    def test_format_metrics_for_analysis(self):
        """Test metrics formatting for LLM"""
        agent = GCSpecialistAgent()
        
        metrics = {
            'young_gc_count': 10,
            'full_gc_count': 2,
            'total_pause_time': 5.5,
            'max_pause_time': 2.5,
            'avg_pause_time': 0.458,
            'heap_before': [1024, 1536, 1800],
            'heap_after': [512, 768, 600]
        }
        
        formatted = agent._format_metrics_for_analysis(metrics)
        
        # Verify formatting
        self.assertIn('Young GC Count: 10', formatted)
        self.assertIn('Full GC Count: 2', formatted)
        self.assertIn('Total Pause Time', formatted)
    
    def test_summarize_metrics(self):
        """Test metrics summarization"""
        agent = GCSpecialistAgent()
        
        metrics = {
            'young_gc_count': 10,
            'full_gc_count': 2,
            'total_pause_time': 5.5,
            'max_pause_time': 2.5,
            'avg_pause_time': 0.458,
            'heap_before': [1024, 1536, 1800]
        }
        
        summary = agent._summarize_metrics(metrics)
        
        # Verify summary structure
        self.assertIn('gc_counts', summary)
        self.assertIn('pause_times', summary)
        self.assertEqual(summary['gc_counts']['young_gc'], 10)
        self.assertEqual(summary['gc_counts']['full_gc'], 2)
    
    def test_generate_summary(self):
        """Test summary generation"""
        agent = GCSpecialistAgent()
        
        state = GCAnalysisState(
            gc_logs="",
            raw_metrics={},
            gc_patterns={},
            memory_issues=[
                {'type': 'Memory Leak', 'severity': 'Critical'},
                {'type': 'Excessive GC', 'severity': 'High'}
            ],
            tuning_recommendations={'jvm_parameters': [], 'gc_algorithm': 'G1GC'},
            analysis_summary="",
            errors=[]
        )
        
        summary = agent._generate_summary(state)
        
        # Verify summary content
        self.assertIn('GC Analysis Summary', summary)
        self.assertIn('Issues Detected: 2', summary)
        self.assertIn('Critical', summary)
    
    @patch('gc_agent.ChatOpenAI')
    def test_analyze_gc_patterns_node(self, mock_llm):
        """Test the analyze_gc_patterns workflow node"""
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = json.dumps({
            'pause_time_analysis': 'Normal pause times',
            'heap_usage_analysis': 'Stable heap usage',
            'old_gen_analysis': 'No growth detected',
            'full_gc_analysis': 'Acceptable frequency',
            'allocation_rate': 'Moderate'
        })
        mock_llm.return_value.invoke.return_value = mock_response
        
        agent = GCSpecialistAgent()
        agent.llm = mock_llm.return_value
        
        state = GCAnalysisState(
            gc_logs=self.sample_gc_log,
            raw_metrics={
                'young_gc_count': 4,
                'full_gc_count': 2,
                'total_pause_time': 2.7,
                'max_pause_time': 1.3,
                'avg_pause_time': 0.45
            },
            gc_patterns={},
            memory_issues=[],
            tuning_recommendations=[],
            analysis_summary="",
            errors=[]
        )
        
        result_state = agent.analyze_gc_patterns(state)
        
        # Verify patterns were analyzed
        self.assertIsNotNone(result_state['gc_patterns'])
        self.assertGreater(len(result_state['gc_patterns']), 0)
    
    @patch('gc_agent.ChatOpenAI')
    def test_detect_memory_issues_node(self, mock_llm):
        """Test the detect_memory_issues workflow node"""
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = json.dumps([
            {
                'type': 'Excessive Full GC',
                'severity': 'High',
                'evidence': 'Multiple Full GCs in short period',
                'impact': 'Application pauses'
            }
        ])
        mock_llm.return_value.invoke.return_value = mock_response
        
        agent = GCSpecialistAgent()
        agent.llm = mock_llm.return_value
        
        state = GCAnalysisState(
            gc_logs=self.problematic_gc_log,
            raw_metrics={'full_gc_count': 4},
            gc_patterns={'full_gc_analysis': 'Too frequent'},
            memory_issues=[],
            tuning_recommendations=[],
            analysis_summary="",
            errors=[]
        )
        
        result_state = agent.detect_memory_issues(state)
        
        # Verify issues were detected
        self.assertIsNotNone(result_state['memory_issues'])
        self.assertGreater(len(result_state['memory_issues']), 0)
    
    @patch('gc_agent.ChatOpenAI')
    def test_recommend_tuning_node(self, mock_llm):
        """Test the recommend_tuning workflow node"""
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = json.dumps({
            'jvm_parameters': [
                {
                    'parameter': '-Xmx',
                    'recommended': '4096m',
                    'justification': 'Increase heap size',
                    'priority': 'High'
                }
            ],
            'gc_algorithm': 'G1GC',
            'summary': 'Recommendations generated'
        })
        mock_llm.return_value.invoke.return_value = mock_response
        
        agent = GCSpecialistAgent()
        agent.llm = mock_llm.return_value
        
        state = GCAnalysisState(
            gc_logs=self.problematic_gc_log,
            raw_metrics={'full_gc_count': 4},
            gc_patterns={'full_gc_analysis': 'Too frequent'},
            memory_issues=[{'type': 'Excessive Full GC', 'severity': 'High'}],
            tuning_recommendations=[],
            analysis_summary="",
            errors=[]
        )
        
        result_state = agent.recommend_tuning(state)
        
        # Verify recommendations were generated
        self.assertIsNotNone(result_state['tuning_recommendations'])
        self.assertIsNotNone(result_state['analysis_summary'])
    
    def test_workflow_structure(self):
        """Test that workflow has correct structure"""
        agent = GCSpecialistAgent()
        
        # Verify workflow exists
        self.assertIsNotNone(agent.workflow)
        
        # Workflow should be compiled
        self.assertTrue(hasattr(agent.workflow, 'invoke'))


class TestGCLogParsing(unittest.TestCase):
    """Test cases for GC log parsing"""
    
    def test_parse_young_gc(self):
        """Test parsing Young GC events"""
        agent = GCSpecialistAgent()
        log = "[GC (Allocation Failure) 2023-01-15T10:30:45.123+0000: 1024K->512K(2048K), 0.0234567 secs]"
        metrics = agent._parse_gc_logs(log)
        
        self.assertEqual(metrics['young_gc_count'], 1)
        self.assertEqual(metrics['full_gc_count'], 0)
    
    def test_parse_full_gc(self):
        """Test parsing Full GC events"""
        agent = GCSpecialistAgent()
        log = "[Full GC (Ergonomics) 2023-01-15T10:31:00.789+0000: 1800K->600K(2048K), 1.2345678 secs]"
        metrics = agent._parse_gc_logs(log)
        
        self.assertEqual(metrics['young_gc_count'], 0)
        self.assertEqual(metrics['full_gc_count'], 1)
    
    def test_parse_multiple_gc_events(self):
        """Test parsing multiple GC events"""
        agent = GCSpecialistAgent()
        log = """
[GC (Allocation Failure) 1024K->512K(2048K), 0.023 secs]
[GC (Allocation Failure) 1536K->768K(2048K), 0.034 secs]
[Full GC (Ergonomics) 1800K->600K(2048K), 1.234 secs]
"""
        metrics = agent._parse_gc_logs(log)
        
        self.assertEqual(metrics['young_gc_count'], 2)
        self.assertEqual(metrics['full_gc_count'], 1)
        self.assertAlmostEqual(metrics['total_pause_time'], 1.291, places=2)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)

# Made with Bob
