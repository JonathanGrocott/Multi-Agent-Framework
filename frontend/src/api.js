/**
 * API client for backend communication
 */

const API_BASE = `http://localhost:8000`;

/**
 * @typedef {Object} Machine
 * @property {string} id
 * @property {string} name
 * @property {string} [description]
 * @property {string[]} capabilities
 * @property {number} agent_count
 */

/**
 * @typedef {Object} ChatMessage
 * @property {'user'|'assistant'} role
 * @property {string} content
 * @property {Date} [timestamp]
 */

/**
 * @typedef {Object} ChatResponse
 * @property {string} response
 * @property {number} agent_count
 * @property {number} execution_time_ms
 * @property {string} machine_id
 * @property {string} timestamp
 */

/**
 * Fetch list of available machines
 * @returns {Promise<Machine[]>}
 */
export async function fetchMachines() {
    const response = await fetch(`${API_BASE}/api/machines`);
    if (!response.ok) {
        throw new Error('Failed to fetch machines');
    }
    const data = await response.json();
    return data.machines;
}

/**
 * Send a chat message to a machine
 * @param {string} machineId
 * @param {string} message
 * @returns {Promise<ChatResponse>}
 */
export async function sendChatMessage(
    machineId,
    message
) {
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
