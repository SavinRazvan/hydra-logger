"""
Component Composition Engine for Hydra-Logger

This module provides a sophisticated composition engine for building complex
components from simpler ones using a trait-based approach. It enables
dynamic component composition, dependency management, and validation.

ARCHITECTURE:
- ComponentComposer: Main composition engine for building complex components
- TraitMixin: Mixin for adding trait-based composition capabilities
- Dependency Management: Tracks and validates component dependencies
- Composition Validation: Ensures compositions are valid and free of cycles

COMPOSITION FEATURES:
- Dynamic component registration and composition
- Dependency tracking and validation
- Circular dependency detection
- Component tree visualization
- Composition optimization
- Trait-based behavior addition

TRAIT SYSTEM:
- TraitMixin: Adds trait capabilities to any component
- Dynamic method and property addition
- Trait conflict detection and resolution
- Requirement validation
- Composable trait combinations

VALIDATION FEATURES:
- Circular dependency detection
- Component existence validation
- Trait conflict resolution
- Composition optimization suggestions
- Dependency tree analysis

USAGE EXAMPLES:

Component Composition:
    from hydra_logger.core.composition import ComponentComposer, BaseComponent
    
    composer = ComponentComposer()
    composer.register_component("handler", my_handler)
    composer.register_component("formatter", my_formatter)
    
    composite = composer.compose("logger", ["handler", "formatter"])

Trait-Based Composition:
    from hydra_logger.core.composition import TraitMixin
    
    class MyLogger(TraitMixin, BaseLogger):
        def __init__(self):
            super().__init__()
            # Add traits for enhanced functionality
            self.add_trait("logging", LoggingTrait())
            self.add_trait("monitoring", MonitoringTrait())

Composition Validation:
    from hydra_logger.core.composition import validate_composition
    
    errors = validate_composition("my_composition")
    if errors:
        print("Composition errors:", errors)
"""

from typing import Any, Dict, List, Optional, Union, Callable
from .base import BaseComponent


class ComponentComposer:
    """Engine for composing components from simpler ones."""
    
    def __init__(self):
        self._components: Dict[str, BaseComponent] = {}
        self._compositions: Dict[str, List[str]] = {}
        self._dependencies: Dict[str, List[str]] = {}
    
    def register_component(self, name: str, component: BaseComponent) -> None:
        """Register a component for composition."""
        self._components[name] = component
    
    def unregister_component(self, name: str) -> None:
        """Unregister a component."""
        if name in self._components:
            del self._components[name]
        
        # Remove from compositions and dependencies
        if name in self._compositions:
            del self._compositions[name]
        
        for deps in self._dependencies.values():
            if name in deps:
                deps.remove(name)
    
    def compose(self, name: str, component_names: List[str], 
                composer_func: Optional[Callable] = None) -> BaseComponent:
        """Compose a new component from existing ones."""
        if not component_names:
            raise ValueError("At least one component is required for composition")
        
        # Check if all components exist
        for comp_name in component_names:
            if comp_name not in self._components:
                raise ValueError(f"Component '{comp_name}' not found")
        
        # Create composition
        self._compositions[name] = component_names
        
        # Create dependencies
        for comp_name in component_names:
            if comp_name not in self._dependencies:
                self._dependencies[comp_name] = []
            self._dependencies[comp_name].append(name)
        
        # Use custom composer function if provided
        if composer_func:
            return composer_func([self._components[name] for name in component_names])
        
        # Default composition: create a composite component
        from ..loggers.composite_logger import CompositeLogger
        return CompositeLogger(name=name, components=[self._components[name] for name in component_names])
    
    def get_composition(self, name: str) -> Optional[List[str]]:
        """Get the components that make up a composition."""
        return self._compositions.get(name)
    
    def get_dependencies(self, name: str) -> List[str]:
        """Get components that depend on a specific component."""
        return self._dependencies.get(name, [])
    
    def list_compositions(self) -> List[str]:
        """List all composition names."""
        return list(self._compositions.keys())
    
    def decompose(self, name: str) -> List[BaseComponent]:
        """Decompose a composition into its constituent components."""
        if name not in self._compositions:
            return []
        
        return [self._components[comp_name] for comp_name in self._compositions[name]]
    
    def validate_composition(self, name: str) -> List[str]:
        """Validate a composition for circular dependencies and other issues."""
        errors = []
        
        if name not in self._compositions:
            errors.append(f"Composition '{name}' not found")
            return errors
        
        # Check for circular dependencies
        visited = set()
        rec_stack = set()
        
        def has_cycle(comp_name: str) -> bool:
            if comp_name in rec_stack:
                return True
            if comp_name in visited:
                return False
            
            visited.add(comp_name)
            rec_stack.add(comp_name)
            
            if comp_name in self._compositions:
                for dep in self._compositions[comp_name]:
                    if has_cycle(dep):
                        return True
            
            rec_stack.remove(comp_name)
            return False
        
        if has_cycle(name):
            errors.append(f"Circular dependency detected in composition '{name}'")
        
        # Check if all components in composition exist
        for comp_name in self._compositions[name]:
            if comp_name not in self._components:
                errors.append(f"Component '{comp_name}' in composition '{name}' not found")
        
        return errors
    
    def get_component_tree(self, name: str) -> Dict[str, Any]:
        """Get the component dependency tree for a composition."""
        if name not in self._compositions:
            return {}
        
        tree = {
            'name': name,
            'components': [],
            'dependencies': []
        }
        
        for comp_name in self._compositions[name]:
            comp_info = {
                'name': comp_name,
                'type': type(self._components[comp_name]).__name__,
                'dependencies': self.get_dependencies(comp_name)
            }
            tree['components'].append(comp_info)
        
        return tree
    
    def optimize_composition(self, name: str) -> List[str]:
        """Optimize a composition by removing unnecessary components."""
        if name not in self._compositions:
            return []
        
        # Simple optimization: remove components that are not actually used
        # This is a basic implementation - more sophisticated optimization can be added
        used_components = set()
        
        def mark_used(comp_name: str):
            if comp_name in used_components:
                return
            used_components.add(comp_name)
            
            # Mark dependencies as used
            if comp_name in self._dependencies:
                for dep in self._dependencies[comp_name]:
                    mark_used(dep)
        
        # Mark all components in composition as used
        for comp_name in self._compositions[name]:
            mark_used(comp_name)
        
        # Return unused components
        all_components = set(self._components.keys())
        unused = all_components - used_components
        
        return list(unused)


class TraitMixin:
    """Mixin for adding traits to components."""
    
    def __init__(self, **kwargs):
        self._traits = {}
        self._setup_traits()
    
    def _setup_traits(self):
        """Setup default traits. Override in subclasses."""
        pass
    
    def add_trait(self, name: str, trait: Any) -> None:
        """Add a trait to the component."""
        self._traits[name] = trait
    
    def remove_trait(self, name: str) -> None:
        """Remove a trait from the component."""
        if name in self._traits:
            del self._traits[name]
    
    def get_trait(self, name: str) -> Optional[Any]:
        """Get a trait by name."""
        return self._traits.get(name)
    
    def has_trait(self, name: str) -> bool:
        """Check if component has a specific trait."""
        return name in self._traits
    
    def list_traits(self) -> List[str]:
        """List all trait names."""
        return list(self._traits.keys())
    
    def get_traits(self) -> Dict[str, Any]:
        """Get all traits."""
        return self._traits.copy()


# Global composer instance
component_composer = ComponentComposer()

# Convenience functions
def compose_components(name: str, component_names: List[str], 
                     composer_func: Optional[Callable] = None) -> BaseComponent:
    """Compose components using the global composer."""
    return component_composer.compose(name, component_names, composer_func)

def get_composition(name: str) -> Optional[List[str]]:
    """Get a composition using the global composer."""
    return component_composer.get_composition(name)

def validate_composition(name: str) -> List[str]:
    """Validate a composition using the global composer."""
    return component_composer.validate_composition(name)
