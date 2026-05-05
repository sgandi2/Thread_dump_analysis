# webMethods Thread Dump Analysis Dashboard

Real-time monitoring dashboard for thread dump analysis system.

## Overview

This dashboard provides comprehensive monitoring and visualization for the webMethods Integration Server thread dump analysis system. It displays real-time metrics, thread analysis, performance graphs, AI insights, and alert history.

## Features

### 1. Overview Panel
- Server health status
- Active thread count
- CPU and memory usage metrics
- Real-time updates

### 2. Thread Analysis Panel
- List of all active threads with status
- Thread state distribution (pie chart)
- Stack trace viewer
- Thread timeline visualization

### 3. Performance Metrics Panel
- CPU usage over time (line chart)
- Memory usage over time (line chart)
- Garbage collection statistics
- Threshold indicators

### 4. AI Insights Panel
- Root cause analysis
- Actionable recommendations
- GC specialist insights
- CPU specialist insights
- Confidence scores

### 5. Alert History Panel
- Historical alert log
- Alert severity indicators
- Resolution status
- Time-to-resolution metrics

## Installation

### Prerequisites
- Python 3.8+
- pip package manager

### Install Dependencies

```bash
pip install streamlit plotly pandas
```

Or install from requirements.txt:

```bash
pip install -r ../requirements.txt
```

## Running the Dashboard

### Basic Usage

```bash
streamlit run dashboard/app.py
```

The dashboard will open in your default browser at `http://localhost:8501`

### With Custom Port

```bash
streamlit run dashboard/app.py --server.port 8502
```

### With Auto-reload

```bash
streamlit run dashboard/app.py --server.runOnSave true
```

## Configuration

### Sidebar Settings

- **Server URL**: Configure webMethods Integration Server endpoint
- **Auto-refresh**: Enable/disable automatic data refresh
- **Refresh Interval**: Set refresh frequency (5-60 seconds)
- **Alert Thresholds**: Configure CPU, memory, and hung thread thresholds

### Environment Variables

Create a `.env` file in the project root:

```env
WEBMETHODS_URL=http://localhost:5555
WEBMETHODS_USER=Administrator
WEBMETHODS_PASSWORD=your_password
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

## Dashboard Components

### File Structure

```
dashboard/
├── app.py                      # Main dashboard application
├── README.md                   # This file
├── components/
│   ├── __init__.py
│   └── metrics.py             # Reusable metric components
└── utils/
    ├── __init__.py
    ├── data_loader.py         # Data loading utilities
    └── visualizations.py      # Chart creation utilities
```

### Component Descriptions

#### `app.py`
Main Streamlit application with all dashboard panels and layouts.

#### `components/metrics.py`
Reusable components for displaying:
- Server health metrics
- Alert cards
- Thread information cards
- Recommendation lists
- GC metrics
- Confidence scores

#### `utils/data_loader.py`
Data loading utilities:
- Load analysis results
- Load active alerts
- Load thread dumps
- Get server metrics
- Get performance history

#### `utils/visualizations.py`
Chart creation functions:
- CPU usage charts
- Memory usage charts
- Thread state pie charts
- Thread timeline
- GC pause time charts
- Alert severity charts

## Integration with Other Agents

The dashboard integrates with:

1. **Monitor Agent** (Tapaswini) - Receives status updates and alerts
2. **Analyzer Agent** (Ranadeep) - Displays analysis results
3. **GC Specialist** (Vinay) - Shows GC insights
4. **CPU Specialist** (Vinay) - Shows CPU insights
5. **Remediation Agent** (Sai) - Displays action logs

## Data Flow

```
Monitor Agent → Dashboard (Status Updates)
Collector Agent → Dashboard (Thread Data)
Analyzer Agent → Dashboard (Analysis Results)
GC Specialist → Dashboard (GC Insights)
CPU Specialist → Dashboard (CPU Insights)
Remediation Agent → Dashboard (Action Logs)
```

## Customization

### Adding New Panels

1. Add a new section in `app.py`:
```python
st.header("🆕 New Panel")
# Your panel code here
```

2. Create helper functions in `utils/` or `components/`

### Modifying Visualizations

Edit `utils/visualizations.py` to customize charts:
- Change colors
- Adjust layouts
- Add new chart types

### Custom Metrics

Add new metrics in `components/metrics.py`:
```python
def display_custom_metric(data: Dict):
    st.metric("Custom Metric", data.get('value'))
```

## Troubleshooting

### Dashboard Won't Start

1. Check Python version: `python --version` (should be 3.8+)
2. Verify dependencies: `pip list | grep streamlit`
3. Check port availability: `netstat -an | grep 8501`

### No Data Displayed

1. Verify data directories exist:
   - `data/analysis_results/`
   - `data/alerts/`
   - `data/thread_dumps/`

2. Check file permissions
3. Verify agent outputs are being written

### Performance Issues

1. Reduce refresh interval
2. Disable auto-refresh
3. Limit historical data range
4. Use data sampling for large datasets

## Development

### Running in Development Mode

```bash
streamlit run dashboard/app.py --server.runOnSave true --server.fileWatcherType poll
```

### Testing

```bash
# Test with sample data
python -c "from dashboard.utils.data_loader import DataLoader; dl = DataLoader(); print(dl.get_server_metrics())"
```

### Adding Features

1. Create feature branch
2. Implement changes
3. Test thoroughly
4. Update documentation
5. Submit for review

## Performance Optimization

- Use `@st.cache_data` for expensive computations
- Implement data pagination for large datasets
- Use incremental updates instead of full refreshes
- Optimize chart rendering with sampling

## Security Considerations

- Never commit credentials to version control
- Use environment variables for sensitive data
- Implement authentication if exposing publicly
- Validate all user inputs
- Use HTTPS in production

## Future Enhancements

- [ ] User authentication
- [ ] Custom dashboard layouts
- [ ] Export reports to PDF
- [ ] Email notifications
- [ ] Mobile-responsive design
- [ ] Dark mode theme
- [ ] Multi-server monitoring
- [ ] Historical trend analysis
- [ ] Predictive alerts

## Support

For issues or questions:
- Check the main project README
- Review IMPLEMENTATION_PLAN.md
- Contact: Bhagwan (Dashboard Developer)

## License

Part of the webMethods Thread Dump Analysis AI Agent System.

---

**Version:** 1.0  
**Last Updated:** 2026-05-05  
**Developer:** Bhagwan