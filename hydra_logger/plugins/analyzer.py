"""
Plugin Analyzer for Hydra-Logger

This module provides comprehensive plugin analysis capabilities including
compatibility checking, performance analysis, dependency validation, and
plugin recommendations. It helps identify optimal plugin configurations
and provides insights for plugin optimization.

FEATURES:
- Plugin compatibility analysis and scoring
- Performance characteristics evaluation
- Dependency validation and requirements checking
- Plugin recommendation engine
- Optimization suggestions and insights

USAGE:
    from hydra_logger.plugins import PluginAnalyzer
    
    # Create plugin analyzer
    analyzer = PluginAnalyzer()
    
    # Analyze a specific plugin
    analysis = analyzer.analyze_plugin("my_plugin")
    
    # Get plugin recommendations
    recommendations = analyzer.get_recommendations()
    
    # Get optimization suggestions
    optimizations = analyzer.optimize_plugins()
"""

import time
import inspect
from typing import Dict, List, Optional, Any, Type
from .base import BasePlugin
from .discovery import PluginDiscovery


class PluginAnalyzer:
    """Plugin analysis and optimization system."""
    
    def __init__(self):
        """Initialize plugin analyzer."""
        self._discovery = PluginDiscovery()
        self._analysis_cache: Dict[str, Dict[str, Any]] = {}
        self._performance_metrics: Dict[str, Dict[str, Any]] = {}
        self._compatibility_rules: Dict[str, List[str]] = {}
        
        # Initialize default compatibility rules
        self._setup_default_compatibility_rules()
    
    def _setup_default_compatibility_rules(self) -> None:
        """Setup default compatibility rules."""
        self._compatibility_rules = {
            'formatter': ['format', 'get_format_name'],
            'handler': ['emit', 'get_handler_type'],
            'security': ['detect_threats', 'get_security_score'],
            'performance': ['track_operation', 'get_performance_stats'],
            'analytics': ['process_event', 'get_insights']
        }
    
    def analyze_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """Analyze a specific plugin for compatibility and performance."""
        if plugin_name in self._analysis_cache:
            return self._analysis_cache[plugin_name]
        
        plugin_class = self._discovery.get_plugin_class(plugin_name)
        if not plugin_class:
            return {
                'compatible': False,
                'reason': 'Plugin not found',
                'error': 'Plugin not discovered'
            }
        
        try:
            analysis = self._perform_analysis(plugin_class)
            self._analysis_cache[plugin_name] = analysis
            return analysis
            
        except Exception as e:
            error_analysis = {
                'compatible': False,
                'reason': f'Analysis failed: {e}',
                'error': str(e)
            }
            self._analysis_cache[plugin_name] = error_analysis
            return error_analysis
    
    def _perform_analysis(self, plugin_class: Type[BasePlugin]) -> Dict[str, Any]:
        """Perform comprehensive plugin analysis."""
        analysis = {
            'compatible': True,
            'type': self._detect_plugin_type(plugin_class),
            'features': self._analyze_features(plugin_class),
            'dependencies': self._analyze_dependencies(plugin_class),
            'performance': self._analyze_performance(plugin_class),
            'compatibility_score': 0,
            'recommendations': []
        }
        
        # Calculate compatibility score
        analysis['compatibility_score'] = self._calculate_compatibility_score(analysis)
        
        # Generate recommendations
        analysis['recommendations'] = self._generate_recommendations(analysis)
        
        # Determine overall compatibility
        analysis['compatible'] = analysis['compatibility_score'] >= 70
        
        return analysis
    
    def _detect_plugin_type(self, plugin_class: Type[BasePlugin]) -> str:
        """Detect the type of plugin."""
        plugin_type = 'generic'
        
        for base_type, required_methods in self._compatibility_rules.items():
            if all(hasattr(plugin_class, method) for method in required_methods):
                plugin_type = base_type
                break
        
        return plugin_type
    
    def _analyze_features(self, plugin_class: Type[BasePlugin]) -> Dict[str, Any]:
        """Analyze plugin features and capabilities."""
        features = {
            'methods': [],
            'properties': [],
            'capabilities': []
        }
        
        # Analyze methods
        for name, method in inspect.getmembers(plugin_class, inspect.isfunction):
            if not name.startswith('_'):
                features['methods'].append(name)
        
        # Analyze properties
        for name, prop in inspect.getmembers(plugin_class, lambda x: isinstance(x, property)):
            if not name.startswith('_'):
                features['properties'].append(name)
        
        # Analyze capabilities based on method presence
        if hasattr(plugin_class, 'process_event'):
            features['capabilities'].append('event_processing')
        if hasattr(plugin_class, 'format'):
            features['capabilities'].append('formatting')
        if hasattr(plugin_class, 'emit'):
            features['capabilities'].append('output_handling')
        if hasattr(plugin_class, 'detect_threats'):
            features['capabilities'].append('security')
        if hasattr(plugin_class, 'track_operation'):
            features['capabilities'].append('performance_monitoring')
        
        return features
    
    def _analyze_dependencies(self, plugin_class: Type[BasePlugin]) -> Dict[str, Any]:
        """Analyze plugin dependencies and requirements."""
        dependencies = {
            'imports': [],
            'requirements': [],
            'external_deps': []
        }
        
        # Get requirements from class attributes
        requirements = getattr(plugin_class, '__requirements__', [])
        dependencies['requirements'] = requirements
        
        # Analyze source code for imports (basic analysis)
        try:
            source = inspect.getsource(plugin_class)
            if 'import ' in source:
                dependencies['imports'] = [line.strip() for line in source.split('\n') 
                                        if line.strip().startswith('import ')]
        except Exception:
            pass
        
        return dependencies
    
    def _analyze_performance(self, plugin_class: Type[BasePlugin]) -> Dict[str, Any]:
        """Analyze plugin performance characteristics."""
        performance = {
            'complexity': 'low',
            'overhead': 'minimal',
            'optimization_potential': 'none'
        }
        
        # Basic complexity analysis based on method count
        method_count = len([name for name, method in inspect.getmembers(plugin_class, inspect.isfunction)
                          if not name.startswith('_')])
        
        if method_count > 20:
            performance['complexity'] = 'high'
            performance['optimization_potential'] = 'significant'
        elif method_count > 10:
            performance['complexity'] = 'medium'
            performance['optimization_potential'] = 'moderate'
        
        return performance
    
    def _calculate_compatibility_score(self, analysis: Dict[str, Any]) -> int:
        """Calculate compatibility score (0-100)."""
        score = 0
        
        # Base score for being a valid plugin
        score += 20
        
        # Type detection bonus
        if analysis['type'] != 'generic':
            score += 15
        
        # Feature completeness bonus
        feature_count = len(analysis['features']['capabilities'])
        score += min(feature_count * 10, 30)
        
        # Performance bonus
        if analysis['performance']['complexity'] == 'low':
            score += 10
        elif analysis['performance']['complexity'] == 'medium':
            score += 5
        
        # Method coverage bonus
        method_count = len(analysis['features']['methods'])
        score += min(method_count * 2, 20)
        
        return min(score, 100)
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations for plugin improvement."""
        recommendations = []
        
        if analysis['compatibility_score'] < 70:
            recommendations.append("Consider implementing more required methods for your plugin type")
        
        if analysis['performance']['complexity'] == 'high':
            recommendations.append("Consider simplifying the plugin to reduce complexity")
        
        if not analysis['features']['capabilities']:
            recommendations.append("Add specific capabilities to make the plugin more useful")
        
        if analysis['type'] == 'generic':
            recommendations.append("Implement type-specific methods to improve compatibility")
        
        return recommendations
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Get plugin recommendations based on current system state."""
        recommendations = []
        
        # Analyze all discovered plugins
        discovered_plugins = self._discovery.list_discovered_plugins()
        
        for plugin_name in discovered_plugins:
            analysis = self.analyze_plugin(plugin_name)
            
            if analysis['compatible'] and analysis['compatibility_score'] >= 80:
                recommendations.append({
                    'plugin': plugin_name,
                    'type': 'recommended',
                    'reason': 'High compatibility and feature completeness',
                    'score': analysis['compatibility_score']
                })
            elif not analysis['compatible']:
                recommendations.append({
                    'plugin': plugin_name,
                    'type': 'avoid',
                    'reason': 'Low compatibility score',
                    'score': analysis['compatibility_score']
                })
        
        # Sort by score
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        return recommendations
    
    def optimize_plugins(self) -> Dict[str, Any]:
        """Provide optimization recommendations for all plugins."""
        optimization_results = {
            'optimized': 0,
            'recommendations': [],
            'performance_improvements': []
        }
        
        discovered_plugins = self._discovery.list_discovered_plugins()
        
        for plugin_name in discovered_plugins:
            analysis = self.analyze_plugin(plugin_name)
            
            if analysis['performance']['optimization_potential'] != 'none':
                optimization_results['performance_improvements'].append({
                    'plugin': plugin_name,
                    'potential': analysis['performance']['optimization_potential'],
                    'current_complexity': analysis['performance']['complexity']
                })
            
            if analysis['recommendations']:
                optimization_results['recommendations'].extend([
                    f"{plugin_name}: {rec}" for rec in analysis['recommendations']
                ])
        
        return optimization_results
    
    def get_analysis_cache(self) -> Dict[str, Dict[str, Any]]:
        """Get the analysis cache."""
        return self._analysis_cache.copy()
    
    def clear_analysis_cache(self) -> None:
        """Clear the analysis cache."""
        self._analysis_cache.clear()
    
    def get_analyzer_stats(self) -> Dict[str, Any]:
        """Get analyzer statistics."""
        return {
            'cached_analyses': len(self._analysis_cache),
            'compatibility_rules': len(self._compatibility_rules),
            'discovered_plugins': len(self._discovery.list_discovered_plugins())
        }
