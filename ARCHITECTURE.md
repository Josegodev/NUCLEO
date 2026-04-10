cat > ARCHITECTURE.md << 'EOF'
# Architecture

## Flow

Request → Planner → ToolRegistry → PolicyEngine → Tool → Response

## Components

### API
Handles HTTP requests

### Planner
Maps user input to tool + payload

### Tool Registry
Resolves tool by name

### Tools
Encapsulated capabilities (echo, system_info)

### Policy Engine
Controls whether tool execution is allowed

## Principles

- Explicit control over execution
- No implicit side effects
- Modular but simple
- No hidden state

## Future

- ExecutionContext
- Multi-step planning
- Safer policy rules
EOF