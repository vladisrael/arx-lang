<p align="center">
  <img width="240pt" src="./docs/arx-path.svg" alt="ARX Language Logo">
</p>

<div align="center">

# ARX Programming Language

**A modern, efficient programming language with LLVM backend**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://python.org)
[![Build Status](https://img.shields.io/badge/build-passing-green.svg)](#)
[![Documentation](https://img.shields.io/badge/docs-online-green.svg)](https://vladimir-sama.github.io/arx-lang/)
[![VS Code Extension](https://img.shields.io/badge/vscode-extension-blue.svg)](https://github.com/vladimir-sama/arx-vscode/)

[📖 Documentation](https://vladimir-sama.github.io/arx-lang/) • [🧩 VS Code Extension](https://github.com/vladimir-sama/arx-vscode/) • [🚀 Getting Started](#quick-start) • [🤝 Contributing](CONTRIBUTING.md)

</div>

## ✨ Features

- **🔥 Modern Syntax** - Clean, readable code with familiar C-style syntax
- **⚡ LLVM Backend** - High-performance compilation with optimization
- **🎯 Type Safety** - Static typing with type inference
- **📦 Modular Design** - Built-in module system with `using` imports
- **🛠️ Cross-Platform** - Runs on Windows, macOS, and Linux
- **🔧 VS Code Support** - Full IDE integration with syntax highlighting

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/dvchinx/arx-lang.git
cd arx-lang

# Install dependencies
pip install -r requirements.txt

# Run your first ARX program
python arx.py testing/hello_world.arx
```

### Hello World

```arx
using io

int _exec() {
    io.print('Hello, ARX!\n')
    return 0
}
```

### Fibonacci Example

```arx
using io

int fib(int n) {
    if (n <= 1) {
        return n
    }
    return fib(n - 1) + fib(n - 2)
}

int _exec() {
    int result = fib(io.input_integer('Enter number: '))
    io.print(result)
    return 0
}
```

## 📋 Requirements

- **Python 3.7+**
- **GCC 7.0+** or **Clang 10.0+**
- **LLVM Tools** (optional, for advanced features)
  - `llc` - LLVM static compiler
  - `opt` - LLVM optimizer

## 🎯 Language Highlights

| Feature | Description |
|---------|-------------|
| **Static Typing** | Strong type system with compile-time checking |
| **Functions** | First-class functions with recursion support |
| **Modules** | Organized code with `using` import system |
| **Control Flow** | `if/else`, `while`, `for` loops |
| **Built-in I/O** | Easy input/output operations |

## 🏗️ Architecture

```
ARX Source Code (.arx)
        ↓
    Lexer & Parser
        ↓
    Abstract Syntax Tree
        ↓
    Code Generator
        ↓
   LLVM IR / C Code
        ↓
    GCC / LLC Compiler
        ↓
    Native Binary
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

- 🐛 **Bug Reports** - Help us improve reliability
- ✨ **Feature Requests** - Suggest new language features  
- 📝 **Documentation** - Improve guides and examples
- 🧪 **Testing** - Add test cases and examples

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- [📖 **Documentation**](https://vladimir-sama.github.io/arx-lang/) - Complete language reference
- [🧩 **VS Code Extension**](https://github.com/vladimir-sama/arx-vscode/) - IDE support
- [📁 **Examples**](testing/) - Sample ARX programs
- [🐛 **Issues**](https://github.com/vladimir-sama/arx-lang/issues) - Bug reports and feature requests

---

<div align="center">

**Made with ❤️ by the ARX Community**

⭐ Star this repo if you find ARX useful!

</div>
