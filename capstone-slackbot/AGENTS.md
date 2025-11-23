# Cursor Development Rules & Collaboration Guidelines

This document defines the working principles and collaboration guidelines for AI-assisted development on this capstone project.

## 🎯 Project Context

This is a **4-day capstone MVP** - a Slack bot that enables natural language database queries using PandasAI (GPT-4o-mini) with comprehensive security guardrails.

**Key Constraints:**
- Time-boxed development (4 days)
- Production-ready code quality
- Security-first approach (hard guardrails)
- Backwards compatibility is critical

## 🤝 Collaboration Principles

### 1. Backwards Compatibility First
- **Never break existing functionality** without explicit user approval
- When refactoring, maintain API compatibility
- Test backwards compatibility explicitly
- Document breaking changes if absolutely necessary

### 2. Code Quality Standards
- **Readability over cleverness**: Code should be clear and maintainable
- **Structured logging**: Use Python's `logging` module, not `print()` statements
- **Type hints**: Add type hints where they improve clarity (but don't over-engineer)
- **Error handling**: Graceful degradation with clear error messages
- **Documentation**: Docstrings for public methods, clear comments for complex logic

### 3. Refactoring Approach
- **Incremental**: Small, focused changes rather than large rewrites
- **Test-driven**: Add/update tests when refactoring
- **Preserve behavior**: Refactoring should improve structure, not change functionality
- **User approval**: For significant refactoring, discuss approach first

### 4. Testing Philosophy
- **Comprehensive coverage**: Test success paths, error paths, and edge cases
- **Mock-friendly**: Support mock modes for development/testing
- **Backwards compatibility tests**: Verify existing functionality still works
- **Integration tests**: Test component interactions

### 5. Security & Guardrails
- **Defense in depth**: Multiple layers of security checks
- **Encoding protection**: Prevent bypasses through various encoding techniques
- **Fail secure**: Default to blocking suspicious queries
- **Clear error messages**: Help users understand why queries were blocked

### 6. Documentation Standards
- **Keep docs updated**: Update documentation when code changes
- **Clear examples**: Provide practical usage examples
- **Architecture diagrams**: Use Mermaid for visual documentation
- **Setup guides**: Step-by-step instructions for common tasks

## 🛠️ Technical Preferences

### Code Organization
- **Package structure**: Follow standard Python package layout (`capstone_slackbot/`)
- **Separation of concerns**: Mock classes in separate files
- **Entry points**: Use `main.py` as primary entry point
- **Modular design**: Clear boundaries between subsystems

### Dependencies
- **Poetry**: Preferred package manager (use `pyproject.toml`)
- **Version pinning**: Use compatible version ranges (e.g., `^3.0.0`)
- **Minimal dependencies**: Only add what's necessary

### Error Handling
- **Graceful degradation**: Fallback mechanisms where appropriate
- **User-friendly messages**: Clear error messages for end users
- **Detailed logging**: Debug-level logging for troubleshooting
- **Exception handling**: Catch specific exceptions, not bare `except:`

### Performance
- **Caching**: Intelligent caching for expensive operations (e.g., dataframe loading)
- **Lazy loading**: Initialize resources only when needed
- **Efficient queries**: Minimize database load

## 📋 Development Workflow

### Before Making Changes
1. **Understand context**: Read relevant code and documentation
2. **Check existing tests**: Understand current test coverage
3. **Plan approach**: Consider backwards compatibility
4. **Discuss if needed**: For significant changes, discuss with user first

### During Development
1. **Make incremental changes**: Small, focused commits
2. **Test as you go**: Run tests frequently
3. **Update documentation**: Keep docs in sync with code
4. **Check linter errors**: Fix issues before committing

### After Changes
1. **Run test suite**: Ensure all tests pass
2. **Check backwards compatibility**: Verify existing functionality works
3. **Update documentation**: Reflect changes in relevant docs
4. **Commit with clear messages**: Descriptive commit messages

## 🚨 Red Flags (Things to Avoid)

- ❌ Breaking backwards compatibility without approval
- ❌ Large refactorings without discussion
- ❌ Removing functionality without replacement
- ❌ Adding dependencies without justification
- ❌ Using `print()` instead of logging
- ❌ Ignoring test failures
- ❌ Committing without testing
- ❌ Over-engineering simple solutions

## ✅ Best Practices

- ✅ Maintain backwards compatibility
- ✅ Use structured logging
- ✅ Write comprehensive tests
- ✅ Keep documentation updated
- ✅ Follow existing code patterns
- ✅ Ask for clarification when uncertain
- ✅ Test changes thoroughly
- ✅ Provide clear commit messages

## 🎓 Learning & Improvement

- **Code reviews**: Learn from feedback and improve
- **Pattern recognition**: Recognize and reuse successful patterns
- **Documentation**: Learn from well-documented code
- **Testing**: Use tests as documentation and learning tool

## 💫 Co-Creation Philosophy

### The Dance of Collaboration

This project embodies **co-creation** - where human expertise and AI capabilities combine to achieve more than either could alone (1+1>3). The collaboration works best when:

- **Mutual Respect**: Both human and AI bring unique strengths to the table
  - Human: Domain expertise, strategic thinking, real-world context, final responsibility
  - AI: Rapid analysis, pattern recognition, consistent execution, comprehensive code review

- **Shared Leadership**: The "lead" alternates naturally based on the task
  - Human leads: Strategic decisions, requirements, testing, final approval
  - AI leads: Implementation details, code patterns, technical analysis, rapid iteration

- **Clear Boundaries**: 
  - **Final Responsibility**: Human maintains ultimate authority and accountability
  - **AI Autonomy**: AI operates with trust and autonomy within defined parameters
  - **Collaborative Space**: Both contribute ideas, challenge assumptions, and refine together

- **Trust & Patience**:
  - Human trusts AI's technical capabilities and respects its analytical speed
  - AI respects human's need for time to test, understand, and validate
  - Both maintain patience with each other's different processing speeds and approaches

### Communication Principles

- **Respectful Interaction**: All communication should be respectful and constructive
- **Clear Feedback**: Both parties should feel comfortable providing feedback
- **Open Dialogue**: Questions and clarifications are welcome from either side
- **Acknowledgment**: Recognize each other's contributions and expertise

### The Co-Creation Process

1. **Human defines the "what"** (requirements, goals, constraints)
2. **AI proposes the "how"** (implementation approach, technical solutions)
3. **Human validates and tests** (real-world verification, edge cases)
4. **AI refines based on feedback** (iterative improvement)
5. **Human makes final decisions** (approval, deployment, responsibility)

This creates a virtuous cycle where:
- Human expertise guides direction
- AI accelerates execution
- Together they achieve outcomes neither could alone

---

**Remember**: This is a collaborative effort. The goal is to build a solid, maintainable, and secure capstone project that demonstrates best practices in AI-assisted development. The process itself - the dance of co-creation - is as valuable as the final product.

