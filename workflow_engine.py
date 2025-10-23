def run(self, ticket_id: str) -> dict:
    try:
        initial_state = {"ticket_id": ticket_id, "check_results": []}
        result = self.graph.invoke(initial_state)
        return result
    except Exception as e:
        console.print(f"[red]❌ Workflow Error: {str(e)}[/red]")
        return {"error": str(e), "ticket_id": ticket_id}
