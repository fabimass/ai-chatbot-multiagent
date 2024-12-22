def filter_agent_history(history, agent_name):
    filtered_history = []

    for entry in history:
        if entry['role'] == 'bot':
            # Include only the specified agent's response in 'content'.
            if agent_name in entry:
                filtered_history.append({
                    "role": "bot",
                    "content": entry[agent_name]
                })
        else:
            # Keep user entries as is.
            filtered_history.append(entry)

    return filtered_history