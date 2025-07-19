# Changelog

All notable changes to the Gemini REPL project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-19

### Overview
Initial release of Gemini REPL - a conversational AI REPL with basic tool support for educational and experimental use.

### Added
- Core REPL event loop with slash commands
- Gemini API integration (migrated to google-genai SDK)
- Context management with conversation persistence
- Session management with UUID-based logging
- Rate limiter with visual countdown display
- Basic tool system for file operations:
  - `read_file` - Read file contents with security sandboxing
  - `write_file` - Create/update files with path validation
  - `list_files` - List directory contents
- Project-specific storage in `~/.gemini/projects/`
- JSONL session logging compatible with Claude's format
- Named sessions support (`--name` flag)
- Session resumption (`--resume` flag)
- Comprehensive security model with path traversal protection
- Rate limit handling for all Gemini models
- Observer pattern for monitoring and experiments

### Security
- Strict path validation preventing directory traversal
- Removed `execute_python` tool due to security concerns
- Sandboxed file operations to current working directory
- No symlink support to prevent escapes

### Known Issues
- Tool dispatch inconsistency (#26) - AI doesn't reliably trigger tools
- Import issues with google-genai in some test environments
- Rate limits can be hit during rapid testing

### Removed
- `execute_python` tool - Removed for security (see #25)

## [Unreleased] - Roadmap to 0.2.0

### Milestones for 0.2.0 - Self-Hosting with Reliable Tool Use

#### 1. Tool Dispatch Reliability
- [ ] Fix inconsistent tool triggering (issue #26)
- [ ] Improve tool descriptions for better AI understanding
- [ ] Add prompt engineering for reliable tool usage
- [ ] Integration tests for tool workflows
- [ ] Tool usage analytics and monitoring

#### 2. Self-Hosting Capabilities
- [ ] Safe source code modification workflow
- [ ] Backup and rollback mechanisms
- [ ] Hot reload without restart
- [ ] Version control integration for changes
- [ ] Safeguards against breaking changes

#### 3. Enhanced Tool System
- [ ] Tool result caching
- [ ] Tool composition and chaining
- [ ] Better error handling and recovery
- [ ] Tool usage examples in prompts
- [ ] Custom tool registration API

#### 4. Production Readiness
- [ ] Comprehensive test coverage (>80%)
- [ ] Performance benchmarks
- [ ] Memory leak detection and fixes
- [ ] Proper async/await implementation
- [ ] Production logging and monitoring

#### 5. Developer Experience
- [ ] Better error messages
- [ ] Tool development guide
- [ ] Self-hosting tutorial
- [ ] API documentation
- [ ] Example tool implementations

### Future Versions

#### 0.3.0 - Advanced Features
- Thinking mode integration
- Multi-modal support (images)
- Plugin system
- Remote tool execution
- Collaborative sessions

#### 0.4.0 - Enterprise Features
- Multi-user support
- Access control
- Audit logging
- Compliance features
- Deployment automation

#### 1.0.0 - Production Ready
- Full test coverage
- Security audit completed
- Performance optimized
- Documentation complete
- Community tools ecosystem
