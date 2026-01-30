/**
 * Agent Mesh Visualization
 * 
 * Priority 7 from Architect Review: Show PBTSO agent collaboration live.
 * Visualizes the multi-agent swarm with orbital layout.
 */

export interface AgentNode {
    id: string;
    name: string;
    role: string;
    status: 'idle' | 'active' | 'waiting' | 'error';
    currentTask?: string;
    color: string;
}

export interface AgentMessage {
    from: string;
    to: string;
    type: 'request' | 'response' | 'broadcast';
    timestamp: Date;
}

const AGENT_COLORS: Record<string, string> = {
    ARCHON: '#8B5CF6',
    'EVAL-PRIME': '#3B82F6',
    KINESIS: '#EC4899',
    COMPILER: '#10B981',
    SENTINEL: '#EF4444',
    TEMPORAL: '#F59E0B',
    DIALECTICA: '#06B6D4',
    FUSION: '#8B5CF6',
};

export class AgentMeshViz {
    private container: HTMLElement;
    private canvas: HTMLCanvasElement;
    private ctx: CanvasRenderingContext2D;
    private agents: AgentNode[] = [];
    private messages: AgentMessage[] = [];
    private animationId: number | null = null;
    private width = 0;
    private height = 0;
    private centerX = 0;
    private centerY = 0;
    private radius = 0;

    constructor(container: HTMLElement) {
        this.container = container;
        this.canvas = document.createElement('canvas');
        this.canvas.className = 'agent-mesh-canvas';
        container.appendChild(this.canvas);
        this.ctx = this.canvas.getContext('2d')!;
        this.resize();
        window.addEventListener('resize', () => this.resize());
    }

    private resize(): void {
        const rect = this.container.getBoundingClientRect();
        this.width = rect.width;
        this.height = rect.height;
        this.canvas.width = this.width * window.devicePixelRatio;
        this.canvas.height = this.height * window.devicePixelRatio;
        this.canvas.style.width = `${this.width}px`;
        this.canvas.style.height = `${this.height}px`;
        this.ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
        this.centerX = this.width / 2;
        this.centerY = this.height / 2;
        this.radius = Math.min(this.width, this.height) * 0.35;
        this.render();
    }

    public setAgents(agents: AgentNode[]): void {
        this.agents = agents;
        this.startAnimation();
    }

    public updateAgentStatus(id: string, status: AgentNode['status'], task?: string): void {
        const agent = this.agents.find(a => a.id === id);
        if (agent) {
            agent.status = status;
            agent.currentTask = task;
        }
    }

    public sendMessage(msg: AgentMessage): void {
        this.messages.push(msg);
        setTimeout(() => {
            const idx = this.messages.indexOf(msg);
            if (idx > -1) this.messages.splice(idx, 1);
        }, 2000);
    }

    private startAnimation(): void {
        if (this.animationId) return;
        const animate = () => {
            this.render();
            this.animationId = requestAnimationFrame(animate);
        };
        animate();
    }

    private render(): void {
        this.ctx.clearRect(0, 0, this.width, this.height);

        // Background
        this.ctx.fillStyle = 'rgba(15, 15, 26, 0.9)';
        this.ctx.fillRect(0, 0, this.width, this.height);

        // Orbital rings
        this.ctx.beginPath();
        this.ctx.arc(this.centerX, this.centerY, this.radius, 0, Math.PI * 2);
        this.ctx.strokeStyle = 'rgba(148, 163, 184, 0.15)';
        this.ctx.lineWidth = 1;
        this.ctx.stroke();

        // Center (ARCHON)
        this.ctx.beginPath();
        this.ctx.arc(this.centerX, this.centerY, 24, 0, Math.PI * 2);
        this.ctx.fillStyle = AGENT_COLORS.ARCHON;
        this.ctx.fill();
        this.ctx.fillStyle = '#fff';
        this.ctx.font = 'bold 10px system-ui';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillText('A', this.centerX, this.centerY);

        // Agents on orbit
        const satelites = this.agents.filter(a => a.id !== 'ARCHON');
        satelites.forEach((agent, i) => {
            const angle = (i / satelites.length) * Math.PI * 2 - Math.PI / 2;
            const x = this.centerX + Math.cos(angle) * this.radius;
            const y = this.centerY + Math.sin(angle) * this.radius;

            // Connection to center
            this.ctx.beginPath();
            this.ctx.moveTo(this.centerX, this.centerY);
            this.ctx.lineTo(x, y);
            this.ctx.strokeStyle = agent.status === 'active' ? agent.color : 'rgba(148, 163, 184, 0.2)';
            this.ctx.lineWidth = agent.status === 'active' ? 2 : 1;
            this.ctx.stroke();

            // Node
            const nodeRadius = agent.status === 'active' ? 18 : 14;
            this.ctx.beginPath();
            this.ctx.arc(x, y, nodeRadius, 0, Math.PI * 2);
            this.ctx.fillStyle = agent.color || '#666';
            this.ctx.globalAlpha = agent.status === 'active' ? 1 : 0.6;
            this.ctx.fill();
            this.ctx.globalAlpha = 1;

            // Pulse for active
            if (agent.status === 'active') {
                const pulse = 1 + Math.sin(Date.now() / 300) * 0.15;
                this.ctx.beginPath();
                this.ctx.arc(x, y, nodeRadius * pulse, 0, Math.PI * 2);
                this.ctx.strokeStyle = agent.color;
                this.ctx.lineWidth = 2;
                this.ctx.globalAlpha = 0.3;
                this.ctx.stroke();
                this.ctx.globalAlpha = 1;
            }

            // Label
            this.ctx.fillStyle = '#fff';
            this.ctx.font = '9px system-ui';
            this.ctx.fillText(agent.name.slice(0, 3).toUpperCase(), x, y);

            // Task tooltip
            if (agent.currentTask && agent.status === 'active') {
                this.ctx.fillStyle = 'rgba(0,0,0,0.7)';
                this.ctx.fillRect(x - 40, y + nodeRadius + 4, 80, 16);
                this.ctx.fillStyle = '#fff';
                this.ctx.font = '8px system-ui';
                this.ctx.fillText(agent.currentTask.slice(0, 12), x, y + nodeRadius + 12);
            }
        });

        // Messages (animated particles)
        this.messages.forEach(msg => {
            const fromAgent = this.agents.find(a => a.id === msg.from) || { id: 'ARCHON' };
            const toAgent = this.agents.find(a => a.id === msg.to);
            if (!toAgent) return;

            const fromIdx = satelites.findIndex(a => a.id === fromAgent.id);
            const toIdx = satelites.findIndex(a => a.id === toAgent.id);

            const fromAngle = fromIdx >= 0 ? (fromIdx / satelites.length) * Math.PI * 2 - Math.PI / 2 : 0;
            const toAngle = toIdx >= 0 ? (toIdx / satelites.length) * Math.PI * 2 - Math.PI / 2 : 0;

            const fromX = fromAgent.id === 'ARCHON' ? this.centerX : this.centerX + Math.cos(fromAngle) * this.radius;
            const fromY = fromAgent.id === 'ARCHON' ? this.centerY : this.centerY + Math.sin(fromAngle) * this.radius;
            const toX = toAgent.id === 'ARCHON' ? this.centerX : this.centerX + Math.cos(toAngle) * this.radius;
            const toY = toAgent.id === 'ARCHON' ? this.centerY : this.centerY + Math.sin(toAngle) * this.radius;

            const elapsed = Date.now() - msg.timestamp.getTime();
            const t = Math.min(1, elapsed / 1000);
            const x = fromX + (toX - fromX) * t;
            const y = fromY + (toY - fromY) * t;

            this.ctx.beginPath();
            this.ctx.arc(x, y, 4, 0, Math.PI * 2);
            this.ctx.fillStyle = msg.type === 'broadcast' ? '#EC4899' : '#3B82F6';
            this.ctx.fill();
        });
    }

    public destroy(): void {
        if (this.animationId) cancelAnimationFrame(this.animationId);
        this.canvas.remove();
    }
}

export function initAgentMesh(container: HTMLElement): AgentMeshViz {
    return new AgentMeshViz(container);
}
