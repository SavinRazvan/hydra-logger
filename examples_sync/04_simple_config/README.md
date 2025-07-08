# 04 - Simple Configuration

## 🎯 Overview

This example demonstrates **simple configuration** with Hydra-Logger. Learn how to use configuration files, environment variables, and different configuration formats to make your logging setup more flexible and maintainable.

## 📚 Learning Path

### 🚀 **Step 1: Basic Configuration** (10 minutes)
- **[01_basic_config.py](modules/01_basic_config.py)** - Simple configuration setup

### 📚 **Step 2: Configuration Files** (15 minutes)
- **[02_yaml_config.py](modules/02_yaml_config.py)** - YAML configuration files
- **[03_toml_config.py](modules/03_toml_config.py)** - TOML configuration files

### ⚡ **Step 3: Advanced Configuration** (15 minutes)
- **[04_env_config.py](modules/04_env_config.py)** - Environment variable substitution
- **[05_config_validation.py](modules/05_config_validation.py)** - Configuration validation

### 💼 **Step 4: Real Applications**
- **[config_manager.py](examples/config_manager.py)** - Configuration management system

## 🚀 Getting Started

### **Step 1: Setup**
```bash
# Install dependencies
pip install -r requirements.txt

# Or install Hydra-Logger directly
pip install hydra-logger
```

### **Step 2: Start Learning**
```bash
# Begin with basic configuration
python modules/01_basic_config.py

# Progress through modules
python modules/02_yaml_config.py
python modules/03_toml_config.py
python modules/04_env_config.py
python modules/05_config_validation.py

# Try real application
python examples/config_manager.py
```

### **Step 3: Run Complete Tutorial**
```bash
# Run the guided tutorial
python main.py
```

## 📊 What You'll Learn

### **Core Concepts**
1. **Basic Configuration** - Simple configuration setup
2. **Configuration Files** - YAML and TOML configuration files
3. **Environment Variables** - Dynamic configuration with environment variables
4. **Configuration Validation** - Validate and test configurations
5. **Configuration Management** - Organize and manage configurations
6. **Real Applications** - Configuration in production systems

### **Use Cases**
- **Development vs Production** - Different configs for different environments
- **Configuration Management** - Version control and deployment automation
- **Environment Variables** - Dynamic configuration based on environment
- **Configuration Validation** - Ensure configurations are correct
- **Configuration Organization** - Structure configurations for teams

## 🎯 Module Structure

### **modules/** - Progressive Learning
Each module builds on previous knowledge:

- **01_basic_config.py** - Simple configuration setup
- **02_yaml_config.py** - YAML configuration files
- **03_toml_config.py** - TOML configuration files
- **04_env_config.py** - Environment variable substitution
- **05_config_validation.py** - Configuration validation

### **examples/** - Real Applications
Working applications that demonstrate practical usage:

- **config_manager.py** - Configuration management system

### **config_examples/** - Configuration Files
Example configuration files in different formats:

- **basic.yaml** - Basic YAML configuration
- **advanced.yaml** - Advanced YAML configuration
- **basic.toml** - Basic TOML configuration
- **advanced.toml** - Advanced TOML configuration
- **env_config.yaml** - Environment-based configuration

### **Expected File Structure**
```
config_examples/
├── basic.yaml              # Basic YAML configuration
├── advanced.yaml           # Advanced YAML configuration
├── basic.toml              # Basic TOML configuration
├── advanced.toml           # Advanced TOML configuration
└── env_config.yaml         # Environment-based configuration

logs/
├── basic_config.log        # Basic configuration logs
├── yaml_config.log         # YAML configuration logs
├── toml_config.log         # TOML configuration logs
├── env_config.log          # Environment configuration logs
└── validation.log          # Configuration validation logs
```

## 🔑 Key Features Demonstrated

### **Configuration Benefits**
- **Flexibility** - Easy to change logging behavior
- **Maintainability** - Separate configuration from code
- **Environment Support** - Different configs for different environments
- **Version Control** - Track configuration changes
- **Team Collaboration** - Share configurations across team

### **Configuration Formats**
- **YAML** - Human-readable, hierarchical structure
- **TOML** - Simple, table-based format
- **JSON** - Machine-readable format
- **Environment Variables** - Dynamic configuration

### **Configuration Features**
- **File Loading** - Load configuration from files
- **Environment Substitution** - Use environment variables
- **Validation** - Validate configuration correctness
- **Error Handling** - Graceful configuration errors
- **Format Detection** - Automatic format detection

## 📋 Prerequisites

### **Required**
- Python 3.7 or higher
- Hydra-Logger installed
- Write permissions for log directories

### **Installation**
```bash
# Install Hydra-Logger
pip install hydra-logger

# Or install in development mode
pip install -e .

# Install optional dependencies for enhanced examples
pip install -r requirements.txt
```

## 🎯 Expected Learning Outcomes

After completing this tutorial, you'll be able to:

### **Basic Configuration**
- ✅ Create simple configurations
- ✅ Understand configuration structure
- ✅ Use different configuration formats
- ✅ Load configurations from files

### **Advanced Configuration**
- ✅ Use environment variables in configurations
- ✅ Validate configurations
- ✅ Handle configuration errors
- ✅ Organize configurations for teams

### **Real-World Applications**
- ✅ Build configuration management systems
- ✅ Create environment-specific configurations
- ✅ Implement configuration validation
- ✅ Follow configuration best practices

## 🧪 Testing Your Knowledge

### **Progressive Testing**
Each module includes:
- ✅ Clear examples with explanations
- ✅ Expected configuration outputs
- ✅ Next steps guidance
- ✅ Key takeaways summary

### **Real Application Testing**
```bash
# Run the configuration manager application
python examples/config_manager.py

# Check the generated log files
ls -la logs/
cat logs/config_manager.log
```

## 📁 Configuration Organization

### **Basic Structure**
```
config_examples/
├── basic.yaml              # Basic YAML configuration
├── advanced.yaml           # Advanced YAML configuration
├── basic.toml              # Basic TOML configuration
├── advanced.toml           # Advanced TOML configuration
└── env_config.yaml         # Environment-based configuration

logs/
├── basic_config.log        # Basic configuration logs
├── yaml_config.log         # YAML configuration logs
├── toml_config.log         # TOML configuration logs
├── env_config.log          # Environment configuration logs
└── validation.log          # Configuration validation logs
```

## 📚 Use Cases

### **Development vs Production**
- Different log levels for different environments
- Different output destinations
- Different configuration complexity
- Environment-specific features

### **Configuration Management**
- Version control for configurations
- Environment-specific configs
- Deployment automation
- Configuration validation

### **Team Collaboration**
- Shared configuration templates
- Standardized configuration formats
- Configuration documentation
- Configuration reviews

### **Deployment Automation**
- Environment-based configuration loading
- Configuration validation in CI/CD
- Configuration deployment strategies
- Configuration monitoring

## 📚 Next Steps

After completing this tutorial:

1. **Explore Other Examples**: Check out the other examples in this directory
2. **Try Multi-Layer Logging**: Explore `05_multiple_layers` for complex logging
3. **Learn Log Rotation**: Try `06_rotation` for log file management
4. **Study Environment Detection**: Try `10_environment_detection` for environment-based configs
5. **Read Documentation**: Visit the main documentation for advanced features

## 🤝 Need Help?

- **Documentation**: Check the main README for comprehensive guides
- **Issues**: Report bugs or request features on GitHub
- **Discussions**: Join the community discussions for help and ideas

---

**Happy Configuration! 🐉** 