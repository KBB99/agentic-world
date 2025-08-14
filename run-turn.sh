#!/bin/bash
# Run simulation turns with various options

# Default: Run 1 turn with simulated decisions
run_single_turn() {
    echo "Running 1 simulation turn..."
    python3 execute-simulation-turn.py --turns 1
}

# Run multiple turns
run_multiple_turns() {
    local turns=${1:-5}
    echo "Running $turns simulation turns..."
    python3 execute-simulation-turn.py --turns $turns
}

# Run with AWS Bedrock AI
run_with_bedrock() {
    local turns=${1:-1}
    echo "Running $turns turn(s) with AWS Bedrock Claude..."
    python3 execute-simulation-turn.py --turns $turns --use-bedrock --verbose
}

# Reset and run
reset_and_run() {
    echo "Resetting world state and running simulation..."
    python3 execute-simulation-turn.py --turns 1 --reset
}

# Show help
show_help() {
    echo "Usage: ./run-turn.sh [OPTION]"
    echo ""
    echo "Options:"
    echo "  single       Run 1 turn (default)"
    echo "  multi [N]    Run N turns (default 5)"
    echo "  bedrock [N]  Run N turns with AWS Bedrock"
    echo "  reset        Reset world and run 1 turn"
    echo "  help         Show this help"
    echo ""
    echo "Examples:"
    echo "  ./run-turn.sh              # Run 1 turn"
    echo "  ./run-turn.sh multi 10     # Run 10 turns"
    echo "  ./run-turn.sh bedrock 3    # Run 3 turns with AI"
    echo "  ./run-turn.sh reset        # Reset and run"
}

# Main script logic
case "${1:-single}" in
    single)
        run_single_turn
        ;;
    multi)
        run_multiple_turns $2
        ;;
    bedrock)
        run_with_bedrock $2
        ;;
    reset)
        reset_and_run
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown option: $1"
        show_help
        exit 1
        ;;
esac