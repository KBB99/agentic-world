// Project by alex_chen
// Writing at library for wifi, skipping meals

class App {
    constructor() {
        this.messages = [];
        this.init();
    }
    
    init() {
        console.log('App initialized by alex_chen');
        this.render();
    }
    
    render() {
        const app = document.getElementById('app');
        app.innerHTML = `
            <h2>Interactive Demo</h2>
            <button onclick="alert('Created by alex_chen!')">Click Me</button>
        `;
    }
}

// Initialize app
const app = new App();