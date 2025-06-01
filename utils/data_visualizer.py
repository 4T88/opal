import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

class DataVisualizer:
    def __init__(self):
        self.color_palette = px.colors.qualitative.Set3
    
    def create_productivity_dashboard(self, analytics_data: Dict) -> Dict[str, go.Figure]:
        """Create a comprehensive productivity dashboard"""
        dashboard = {}
        
        # Task completion rate over time
        if 'completion_rate' in analytics_data:
            dashboard['completion_rate'] = self._create_completion_rate_chart(analytics_data)
        
        # Task distribution by category
        if 'common_categories' in analytics_data:
            dashboard['category_distribution'] = self._create_category_distribution_chart(analytics_data)
        
        # Productivity by time of day
        if 'most_productive_hours' in analytics_data:
            dashboard['productivity_by_hour'] = self._create_productivity_by_hour_chart(analytics_data)
        
        # Task complexity distribution
        if 'task_complexity_distribution' in analytics_data:
            dashboard['complexity_distribution'] = self._create_complexity_distribution_chart(analytics_data)
        
        return dashboard
    
    def _create_completion_rate_chart(self, analytics_data: Dict) -> go.Figure:
        """Create a line chart showing task completion rate over time"""
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            y=[analytics_data['completion_rate']],
            mode='lines+markers',
            name='Completion Rate',
            line=dict(color=self.color_palette[0], width=2)
        ))
        
        fig.update_layout(
            title='Task Completion Rate',
            xaxis_title='Time',
            yaxis_title='Completion Rate (%)',
            template='plotly_white'
        )
        
        return fig
    
    def _create_category_distribution_chart(self, analytics_data: Dict) -> go.Figure:
        """Create a pie chart showing task distribution by category"""
        categories = json.loads(analytics_data['common_categories']) if isinstance(analytics_data['common_categories'], str) else analytics_data['common_categories']
        
        fig = go.Figure(data=[go.Pie(
            labels=list(categories.keys()),
            values=list(categories.values()),
            hole=.3,
            marker_colors=self.color_palette
        )])
        
        fig.update_layout(
            title='Task Distribution by Category',
            template='plotly_white'
        )
        
        return fig
    
    def _create_productivity_by_hour_chart(self, analytics_data: Dict) -> go.Figure:
        """Create a bar chart showing productivity by hour of day"""
        hours = json.loads(analytics_data['most_productive_hours']) if isinstance(analytics_data['most_productive_hours'], str) else analytics_data['most_productive_hours']
        
        fig = go.Figure(data=[go.Bar(
            x=list(hours.keys()),
            y=list(hours.values()),
            marker_color=self.color_palette[2]
        )])
        
        fig.update_layout(
            title='Productivity by Hour of Day',
            xaxis_title='Hour',
            yaxis_title='Productivity Score',
            template='plotly_white'
        )
        
        return fig
    
    def _create_complexity_distribution_chart(self, analytics_data: Dict) -> go.Figure:
        """Create a histogram showing task complexity distribution"""
        complexity = json.loads(analytics_data['task_complexity_distribution']) if isinstance(analytics_data['task_complexity_distribution'], str) else analytics_data['task_complexity_distribution']
        
        fig = go.Figure(data=[go.Bar(
            x=list(complexity.keys()),
            y=list(complexity.values()),
            marker_color=self.color_palette[3]
        )])
        
        fig.update_layout(
            title='Task Complexity Distribution',
            xaxis_title='Complexity Score',
            yaxis_title='Number of Tasks',
            template='plotly_white'
        )
        
        return fig
    
    def create_task_timeline(self, tasks: List[Dict]) -> go.Figure:
        """Create a Gantt chart showing task timeline"""
        df = pd.DataFrame(tasks)
        
        fig = go.Figure()
        
        for i, task in df.iterrows():
            fig.add_trace(go.Bar(
                x=[task['estimated_duration']],
                y=[task['title']],
                orientation='h',
                name=task['category'],
                marker_color=self.color_palette[i % len(self.color_palette)],
                text=[f"Priority: {task['priority']}"],
                hovertemplate="<b>%{y}</b><br>" +
                            "Duration: %{x} minutes<br>" +
                            "%{text}<br>" +
                            "<extra></extra>"
            ))
        
        fig.update_layout(
            title='Task Timeline',
            xaxis_title='Duration (minutes)',
            yaxis_title='Task',
            template='plotly_white',
            showlegend=False
        )
        
        return fig
    
    def create_productivity_heatmap(self, analytics_data: Dict) -> go.Figure:
        """Create a heatmap showing productivity patterns"""
        if 'most_productive_hours' not in analytics_data:
            return None
        
        hours = json.loads(analytics_data['most_productive_hours']) if isinstance(analytics_data['most_productive_hours'], str) else analytics_data['most_productive_hours']
        
        # Create a 24x7 matrix for hours and days
        data = [[0 for _ in range(7)] for _ in range(24)]
        
        # Fill in the data
        for hour, productivity in hours.items():
            hour = int(hour)
            for day in range(7):
                data[hour][day] = productivity
        
        fig = go.Figure(data=go.Heatmap(
            z=data,
            x=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
            y=list(range(24)),
            colorscale='Viridis'
        ))
        
        fig.update_layout(
            title='Productivity Heatmap',
            xaxis_title='Day',
            yaxis_title='Hour',
            template='plotly_white'
        )
        
        return fig
    
    def create_performance_metrics(self, analytics_data: Dict) -> Dict[str, go.Figure]:
        """Create performance metric visualizations"""
        metrics = {}
        
        # Completion rate gauge
        if 'completion_rate' in analytics_data:
            metrics['completion_rate_gauge'] = self._create_gauge_chart(
                analytics_data['completion_rate'],
                'Task Completion Rate',
                '%'
            )
        
        # Productivity score gauge
        if 'productivity_score' in analytics_data:
            metrics['productivity_gauge'] = self._create_gauge_chart(
                analytics_data['productivity_score'],
                'Productivity Score',
                'points'
            )
        
        # Streak counter
        if 'current_streak' in analytics_data:
            metrics['streak_counter'] = self._create_streak_counter(
                analytics_data['current_streak'],
                analytics_data.get('longest_streak', 0)
            )
        
        return metrics
    
    def _create_gauge_chart(self, value: float, title: str, unit: str) -> go.Figure:
        """Create a gauge chart for metrics"""
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=value,
            title={'text': title},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': self.color_palette[0]},
                'steps': [
                    {'range': [0, 33], 'color': "lightgray"},
                    {'range': [33, 66], 'color': "gray"},
                    {'range': [66, 100], 'color': "darkgray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        fig.update_layout(
            template='plotly_white',
            height=300
        )
        
        return fig
    
    def _create_streak_counter(self, current_streak: int, longest_streak: int) -> go.Figure:
        """Create a streak counter visualization"""
        fig = go.Figure()
        
        # Current streak
        fig.add_trace(go.Indicator(
            mode="number",
            value=current_streak,
            title={'text': "Current Streak"},
            domain={'row': 0, 'column': 0}
        ))
        
        # Longest streak
        fig.add_trace(go.Indicator(
            mode="number",
            value=longest_streak,
            title={'text': "Longest Streak"},
            domain={'row': 0, 'column': 1}
        ))
        
        fig.update_layout(
            grid={'rows': 1, 'columns': 2},
            template='plotly_white',
            height=200
        )
        
        return fig
    
    def create_task_analysis_report(self, tasks: List[Dict]) -> Dict[str, go.Figure]:
        """Create a comprehensive task analysis report"""
        report = {}
        
        if not tasks:
            return report
        
        df = pd.DataFrame(tasks)
        
        # Task status distribution
        if 'status' in df.columns:
            report['status_distribution'] = self._create_status_distribution_chart(df)
        
        # Task priority distribution
        if 'priority' in df.columns:
            report['priority_distribution'] = self._create_priority_distribution_chart(df)
        
        # Task duration analysis
        if 'estimated_duration' in df.columns:
            report['duration_analysis'] = self._create_duration_analysis_chart(df)
        
        # Task category analysis
        if 'category' in df.columns:
            report['category_analysis'] = self._create_category_analysis_chart(df)
        
        return report
    
    def _create_status_distribution_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create a pie chart showing task status distribution"""
        status_counts = df['status'].value_counts()
        
        fig = go.Figure(data=[go.Pie(
            labels=status_counts.index,
            values=status_counts.values,
            hole=.3,
            marker_colors=self.color_palette
        )])
        
        fig.update_layout(
            title='Task Status Distribution',
            template='plotly_white'
        )
        
        return fig
    
    def _create_priority_distribution_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create a bar chart showing task priority distribution"""
        priority_counts = df['priority'].value_counts().sort_index()
        
        fig = go.Figure(data=[go.Bar(
            x=priority_counts.index,
            y=priority_counts.values,
            marker_color=self.color_palette[1]
        )])
        
        fig.update_layout(
            title='Task Priority Distribution',
            xaxis_title='Priority Level',
            yaxis_title='Number of Tasks',
            template='plotly_white'
        )
        
        return fig
    
    def _create_duration_analysis_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create a box plot showing task duration distribution"""
        fig = go.Figure()
        
        fig.add_trace(go.Box(
            y=df['estimated_duration'],
            name='Estimated Duration',
            marker_color=self.color_palette[2]
        ))
        
        if 'actual_duration' in df.columns:
            fig.add_trace(go.Box(
                y=df['actual_duration'],
                name='Actual Duration',
                marker_color=self.color_palette[3]
            ))
        
        fig.update_layout(
            title='Task Duration Analysis',
            yaxis_title='Duration (minutes)',
            template='plotly_white'
        )
        
        return fig
    
    def _create_category_analysis_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create a stacked bar chart showing task category analysis"""
        category_status = pd.crosstab(df['category'], df['status'])
        
        fig = go.Figure()
        
        for status in category_status.columns:
            fig.add_trace(go.Bar(
                x=category_status.index,
                y=category_status[status],
                name=status,
                marker_color=self.color_palette[list(category_status.columns).index(status) % len(self.color_palette)]
            ))
        
        fig.update_layout(
            title='Task Category Analysis',
            xaxis_title='Category',
            yaxis_title='Number of Tasks',
            template='plotly_white',
            barmode='stack'
        )
        
        return fig 