# Contributing to ARX Language

Thank you for your interest in contributing to ARX! We welcome contributions from developers of all skill levels.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Issue Reporting](#issue-reporting)
- [Community Guidelines](#community-guidelines)

## Getting Started

ARX is a programming language with its own compiler and standard library. Before contributing, please:

1. Read our [documentation](https://vladimir-sama.github.io/arx-lang/)
2. Try running some examples from the `testing/` directory
3. Familiarize yourself with the codebase structure

## Development Setup

### Prerequisites

- **Python 3.7 or higher**
- **C Compiler**: GCC 7.0+ or Clang 10.0+
- **LLVM Tools** (optional but recommended):
  - `llc` (LLVM static compiler) for IR compilation
  - `opt` (LLVM optimizer) for code optimization
- **Git** for version control

#### Installing GCC

**On Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install gcc build-essential
```

**On CentOS/RHEL/Fedora:**
```bash
# CentOS/RHEL
sudo yum install gcc gcc-c++ make
# Fedora
sudo dnf install gcc gcc-c++ make
```

**On macOS:**
```bash
# Install Xcode Command Line Tools
xcode-select --install
# Or install via Homebrew
brew install gcc
```

**On Windows:**
- Install [MinGW-w64](https://www.mingw-w64.org/) or [TDM-GCC](https://jmeubank.github.io/tdm-gcc/)
- Or use [Visual Studio Build Tools](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022)

#### Installing LLVM (Recommended)

**On Ubuntu/Debian:**
```bash
sudo apt install llvm llvm-dev clang
```

**On CentOS/RHEL/Fedora:**
```bash
# CentOS/RHEL
sudo yum install llvm llvm-devel clang
# Fedora
sudo dnf install llvm llvm-devel clang
```

**On macOS:**
```bash
brew install llvm
# Add to PATH
export PATH="/opt/homebrew/opt/llvm/bin:$PATH"
```

**On Windows:**
- Download pre-built binaries from [LLVM Releases](https://releases.llvm.org/)
- Or install via [Chocolatey](https://chocolatey.org/): `choco install llvm`

#### Verifying Installation

After installation, verify your tools are working:

```bash
# Check GCC
gcc --version

# Check LLVM tools (if installed)
llc --version
opt --version
clang --version

# Check Python
python --version
```

### Setup Instructions

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/arx-lang.git
   cd arx-lang
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Test the installation:
   ```bash
   python arx.py testing/hello_world.arx
   ```

5. (Optional) Test LLVM integration:
   ```bash
   # Test if ARX can generate LLVM IR and compile with LLC
   python arx.py --emit-llvm testing/fibonacci.arx
   # This should generate fibonacci.ll (LLVM IR)
   
   # Compile LLVM IR to object file
   llc fibonacci.ll -o fibonacci.o
   
   # Link with C runtime (if applicable)
   gcc fibonacci.o -o fibonacci
   ```

## How to Contribute

### Areas for Contribution

- **Language Features**: New syntax, operators, or language constructs
- **Standard Library**: Built-in functions and modules
- **Compiler Improvements**: 
  - LLVM IR generation and optimization
  - GCC backend improvements
  - Error handling and diagnostics
  - Code generation optimizations
- **LLVM Integration**:
  - LLVM IR emission improvements
  - Integration with LLVM optimization passes
  - Target-specific code generation
  - Debugging information generation
- **Documentation**: User guides, API documentation, examples
- **Testing**: Unit tests, integration tests, example programs
- **Tooling**: VS Code extension, debugging tools, formatters

### Types of Contributions

1. **Bug Fixes**: Fix existing issues or unexpected behavior
2. **Feature Additions**: Implement new language features or library functions
3. **Performance Improvements**: Optimize compilation or runtime performance
4. **Documentation**: Improve existing docs or add new content
5. **Tests**: Add test cases for better coverage

## Code Style Guidelines

### Python Code (Compiler)

- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings to all public functions and classes
- Keep functions focused and small
- Use type hints where appropriate

Example:
```python
def parse_expression(self, tokens: List[Token]) -> ExpressionNode:
    """Parse a mathematical or logical expression from tokens.
    
    Args:
        tokens: List of lexical tokens to parse
        
    Returns:
        ExpressionNode representing the parsed expression
    """
    # Implementation here
```

### C Code (Runtime Library)

- Use K&R or Allman brace style consistently
- Use meaningful variable names
- Add comments for complex logic
- Follow existing naming conventions
- Include proper header guards

Example:
```c
/**
 * Concatenate two strings and return the result
 * @param str1 First string
 * @param str2 Second string
 * @return Newly allocated concatenated string
 */
char* string_concat(const char* str1, const char* str2) {
    // Implementation here
}
```

### ARX Test Code

- Use descriptive test names
- Include comments explaining what is being tested
- Test both positive and negative cases
- Keep tests simple and focused

## Testing

### Running Tests

Test your changes using the example programs:

```bash
# Run all tests
python test_runner.py

# Run specific test
python arx.py testing/fibonacci.arx

# Test compiler components
python -m unittest arx_lib.test_lexer
python -m unittest arx_lib.test_parser

# Test LLVM IR generation (if LLVM is available)
python arx.py --emit-llvm testing/fibonacci.arx
llc fibonacci.ll -o fibonacci.o
gcc fibonacci.o -o fibonacci && ./fibonacci

# Test different optimization levels
python arx.py --optimize -O2 testing/fibonacci.arx
python arx.py --emit-llvm --optimize -O3 testing/fibonacci.arx

# Cross-compilation testing (if multiple targets available)
python arx.py --target x86_64 testing/hello_world.arx
python arx.py --target arm64 testing/hello_world.arx
```

### Adding Tests

1. **Language Tests**: Add `.arx` files to the `testing/` directory
2. **Unit Tests**: Add Python test files for compiler components
3. **Integration Tests**: Test complete compilation and execution workflows

### Test Coverage

Ensure your changes include appropriate tests:
- New language features should have example programs
- Bug fixes should include regression tests
- API changes should have unit tests
- LLVM IR generation tests for backend changes
- Cross-platform compilation tests when applicable

### Debugging Compilation Issues

When working on compiler improvements, use these debugging techniques:

```bash
# Generate LLVM IR for inspection
python arx.py --emit-llvm --no-optimize testing/debug_example.arx

# View generated LLVM IR
cat debug_example.ll

# Use LLVM tools for analysis
opt -analyze -basicaa -loops debug_example.ll
llvm-dis debug_example.bc  # if working with bitcode

# Debug with GCC
python arx.py --emit-c testing/debug_example.arx
gcc -g -O0 debug_example.c -o debug_example
gdb ./debug_example

# Memory analysis with Valgrind (Linux/macOS)
valgrind --leak-check=full ./debug_example
```

## Submitting Changes

### Pull Request Process

1. **Create a Feature Branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**:
   - Write code following the style guidelines
   - Add tests for your changes
   - Update documentation if needed

3. **Test Your Changes**:
   ```bash
   # Run existing tests
   python test_runner.py
   
   # Test your specific changes
   python arx.py your_test_file.arx
   ```

4. **Commit Your Changes**:
   ```bash
   git add .
   git commit -m "feat: brief description"
   ```

5. **Push and Create PR**:
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a Pull Request on GitHub.

### Commit Message Guidelines

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

Examples:
```
Add support for nested function calls

- Implement function call parsing in parser.py
- Add test cases for nested scenarios
- Update documentation

Fixes #123
```

### Pull Request Requirements

Your PR should:
- [ ] Have a clear title and description
- [ ] Include tests for new functionality
- [ ] Pass all existing tests
- [ ] Follow code style guidelines
- [ ] Update documentation if needed
- [ ] Reference related issues

## Compiler Backend Development

### Working with LLVM Backend

When contributing to the LLVM backend:

1. **LLVM IR Generation**:
   - Follow LLVM IR best practices
   - Use appropriate LLVM intrinsics for ARX language features
   - Ensure type safety in IR generation
   - Test with different optimization levels

2. **Optimization Passes**:
   - Leverage existing LLVM optimization passes
   - Implement ARX-specific optimizations when beneficial
   - Profile performance impact of optimizations

3. **Target Support**:
   - Test on multiple architectures (x86_64, ARM64, etc.)
   - Handle target-specific features appropriately
   - Maintain cross-compilation capabilities

### Working with GCC Backend

When contributing to the GCC integration:

1. **C Code Generation**:
   - Generate clean, readable C code
   - Follow C standards (C99/C11)
   - Avoid undefined behavior
   - Use appropriate GCC attributes and pragmas

2. **Runtime Integration**:
   - Ensure compatibility with the C runtime library
   - Handle memory management correctly
   - Implement proper error handling

### Backend Testing Best Practices

```bash
# Test both backends
python arx.py --backend llvm testing/example.arx
python arx.py --backend gcc testing/example.arx

# Compare outputs
python arx.py --backend llvm -o example_llvm testing/example.arx
python arx.py --backend gcc -o example_gcc testing/example.arx
diff <(./example_llvm) <(./example_gcc)

# Performance comparison
time ./example_llvm
time ./example_gcc

# Binary size comparison
ls -la example_llvm example_gcc
```

## Issue Reporting

### Before Creating an Issue

1. Check if the issue already exists
2. Try to reproduce the issue with a minimal example
3. Check the documentation for expected behavior

### Bug Reports

Include:
- ARX version or commit hash
- Operating system and version
- Python version
- Minimal code example that reproduces the issue
- Expected vs actual behavior
- Error messages or stack traces

### Feature Requests

Include:
- Clear description of the proposed feature
- Use cases and examples
- How it fits with existing language design
- Potential implementation approach (if known)

## Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Help newcomers learn and contribute
- Focus on what is best for the community

### Getting Help

- Create an issue for questions about contributing
- Check existing documentation and issues first
- Be patient when waiting for responses
- Provide context and examples when asking for help

### Recognition

Contributors will be recognized in:
- Git commit history
- Release notes for significant contributions
- Contributors section (if we add one)

## Development Workflow

### Working on Issues

1. Comment on the issue to indicate you're working on it
2. Ask questions if requirements are unclear
3. Provide regular updates on progress
4. Request help if you get stuck

### Code Review Process

1. All changes must be reviewed before merging
2. Address reviewer feedback promptly
3. Be open to suggestions and improvements
4. Update your PR based on feedback

### Release Process

- Contributions are merged to the `main` branch
- Regular releases are tagged with version numbers
- Breaking changes are clearly documented
- Migration guides are provided when needed

## Resources

- [Project Documentation](https://vladimir-sama.github.io/arx-lang/)
- [VS Code Extension](https://github.com/vladimir-sama/arx-vscode/)
- [Language Examples](./testing/)
- [Issue Tracker](https://github.com/dvchinx/arx-lang/issues)

Thank you for contributing to ARX! 🚀