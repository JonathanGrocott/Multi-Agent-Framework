/**
 * API client for backend communication
 */

const API_BASE = http://localhost:8000`;

export interface Machine {
    id: string;
    name: string;
    description?: string;
    capabilities: string[];
    agent_count: number;
}

export interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    timestamp?: Date;
}

export interface ChatResponse {
    response: string;
    agent_count: number;
    execution_time_ms: number;
    machine_id: string;
    timestamp: string;
}

/**
 * Fetch list of available machines
 */
export async function fetchMachines(): Promise<Machine[]> {
    const response = await fetch(`${API_BASE}/api/machines`);
    if (!response.ok) {
        throw new Error('Failed to fetch machines');
    }
    const data = await response.json();
    return data.machines;
}

/**
 * Send a chat message to a machine
 */
export async function sendChatMessage(
    machineId: string,
    message: string
): Promise<ChatResponse> {
    const response = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            machine_id: machineId,
            message,
            user_id: 'web-user',
        }),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to send message');
    }

    return response.json();
}
