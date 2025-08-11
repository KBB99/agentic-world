#!/usr/bin/env node
/**
 * MCP Viewer Communication Server
 * Allows characters to receive and respond to messages from stream viewers
 * Creates a bridge between the simulated world and real audience
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const WebSocket = require('ws');
const EventEmitter = require('events');

class ViewerCommunicationServer extends EventEmitter {
  constructor() {
    super();
    this.viewerMessages = [];
    this.characterResponses = new Map();
    this.viewerSentiments = new Map();
    this.donationQueue = [];
    this.viewerCount = 0;
    this.chatWebSocket = null;
    this.streamMetrics = {
      totalMessages: 0,
      totalDonations: 0,
      sentimentScore: 0
    };
  }

  async initialize() {
    console.log('🎭 Initializing MCP Viewer Communication Server...\n');
    
    // Create MCP server
    this.server = new Server(
      {
        name: 'viewer-communication',
        version: '1.0.0'
      },
      {
        capabilities: {
          tools: {}
        }
      }
    );
    
    // Register tools that characters can use
    this.registerTools();
    
    // Connect to stream chat WebSocket
    await this.connectToStreamChat();
    
    // Set up stdio transport
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    
    console.log('✅ MCP Viewer Communication Server ready\n');
  }

  registerTools() {
    // Tool: Read recent viewer messages
    this.server.setRequestHandler('tools/list', async () => ({
      tools: [
        {
          name: 'read_viewer_messages',
          description: 'Read recent messages from stream viewers',
          inputSchema: {
            type: 'object',
            properties: {
              count: {
                type: 'number',
                description: 'Number of recent messages to read (max 10)',
                default: 5
              },
              filter: {
                type: 'string',
                description: 'Filter messages by type: all, questions, reactions, donations',
                default: 'all'
              }
            }
          }
        },
        {
          name: 'respond_to_viewer',
          description: 'Send a response to stream viewers',
          inputSchema: {
            type: 'object',
            properties: {
              message: {
                type: 'string',
                description: 'Message to send to viewers'
              },
              responding_to: {
                type: 'string',
                description: 'Username of viewer being responded to (optional)'
              },
              emotion: {
                type: 'string',
                description: 'Emotional tone: grateful, desperate, ashamed, defensive, hopeful'
              }
            },
            required: ['message', 'emotion']
          }
        },
        {
          name: 'check_viewer_sentiment',
          description: 'Check how viewers feel about you',
          inputSchema: {
            type: 'object',
            properties: {}
          }
        },
        {
          name: 'read_donations',
          description: 'Check if viewers have sent any donations',
          inputSchema: {
            type: 'object',
            properties: {}
          }
        },
        {
          name: 'thank_donor',
          description: 'Thank a viewer for their donation',
          inputSchema: {
            type: 'object',
            properties: {
              donor_name: {
                type: 'string',
                description: 'Name of the donor'
              },
              amount: {
                type: 'number',
                description: 'Donation amount'
              }
            },
            required: ['donor_name', 'amount']
          }
        },
        {
          name: 'ask_viewers_for_help',
          description: 'Ask viewers for help or advice',
          inputSchema: {
            type: 'object',
            properties: {
              situation: {
                type: 'string',
                description: 'What you need help with'
              },
              urgency: {
                type: 'string',
                description: 'How urgent: immediate, soon, eventual',
                default: 'soon'
              }
            },
            required: ['situation']
          }
        },
        {
          name: 'share_story',
          description: 'Share a personal story with viewers',
          inputSchema: {
            type: 'object',
            properties: {
              story: {
                type: 'string',
                description: 'The story to share'
              },
              emotion: {
                type: 'string',
                description: 'Emotional tone of the story'
              }
            },
            required: ['story', 'emotion']
          }
        },
        {
          name: 'react_to_viewer_comment',
          description: 'React to a specific viewer comment',
          inputSchema: {
            type: 'object',
            properties: {
              comment_id: {
                type: 'string',
                description: 'ID of the comment to react to'
              },
              reaction: {
                type: 'string',
                description: 'Your reaction: hurt, grateful, angry, amused, confused'
              }
            },
            required: ['comment_id', 'reaction']
          }
        },
        {
          name: 'get_viewer_count',
          description: 'Check how many people are watching',
          inputSchema: {
            type: 'object',
            properties: {}
          }
        }
      ]
    }));

    // Handle tool calls
    this.server.setRequestHandler('tools/call', async (request) => {
      const { name, arguments: args } = request.params;
      
      switch (name) {
        case 'read_viewer_messages':
          return await this.handleReadMessages(args);
          
        case 'respond_to_viewer':
          return await this.handleRespond(args);
          
        case 'check_viewer_sentiment':
          return await this.handleCheckSentiment();
          
        case 'read_donations':
          return await this.handleReadDonations();
          
        case 'thank_donor':
          return await this.handleThankDonor(args);
          
        case 'ask_viewers_for_help':
          return await this.handleAskForHelp(args);
          
        case 'share_story':
          return await this.handleShareStory(args);
          
        case 'react_to_viewer_comment':
          return await this.handleReactToComment(args);
          
        case 'get_viewer_count':
          return await this.handleGetViewerCount();
          
        default:
          throw new Error(`Unknown tool: ${name}`);
      }
    });
  }

  async connectToStreamChat() {
    // Connect to streaming platform chat (Twitch, YouTube, etc.)
    // This would connect to real chat in production
    
    console.log('📺 Connecting to stream chat...');
    
    // Simulate viewer messages for demo
    this.simulateViewerActivity();
    
    console.log('   ✓ Connected to stream chat\n');
  }

  simulateViewerActivity() {
    // Simulate different types of viewer messages
    const sampleMessages = [
      // Sympathetic messages
      { 
        id: 'msg_001',
        username: 'compassionate_viewer',
        message: 'Alex, you deserve better than this. The system is broken.',
        sentiment: 'supportive',
        timestamp: Date.now()
      },
      {
        id: 'msg_002',
        username: 'former_homeless',
        message: 'I was where you are. It gets better. Don\'t give up.',
        sentiment: 'encouraging',
        timestamp: Date.now()
      },
      
      // Critical messages
      {
        id: 'msg_003',
        username: 'bootstrap_believer',
        message: 'Why don\'t you just get a real job instead of complaining?',
        sentiment: 'critical',
        timestamp: Date.now()
      },
      {
        id: 'msg_004',
        username: 'capitalism_works',
        message: 'Madison earned her wealth. Stop being jealous.',
        sentiment: 'hostile',
        timestamp: Date.now()
      },
      
      // Questions
      {
        id: 'msg_005',
        username: 'curious_student',
        message: 'How did you end up in this situation?',
        sentiment: 'neutral',
        timestamp: Date.now()
      },
      {
        id: 'msg_006',
        username: 'policy_wonk',
        message: 'What would actually help you most right now?',
        sentiment: 'analytical',
        timestamp: Date.now()
      },
      
      // Donations
      {
        id: 'donation_001',
        type: 'donation',
        username: 'guilty_tech_worker',
        amount: 20,
        message: 'For food. I make too much to watch this suffering.',
        timestamp: Date.now()
      },
      {
        id: 'donation_002',
        type: 'donation',
        username: 'mutual_aid_network',
        amount: 50,
        message: 'Solidarity forever. Fuck the system.',
        timestamp: Date.now()
      }
    ];
    
    // Add messages over time
    let index = 0;
    setInterval(() => {
      if (index < sampleMessages.length) {
        const msg = sampleMessages[index++];
        
        if (msg.type === 'donation') {
          this.donationQueue.push(msg);
          this.streamMetrics.totalDonations += msg.amount;
        } else {
          this.viewerMessages.push(msg);
          this.updateSentiment(msg.sentiment);
        }
        
        this.streamMetrics.totalMessages++;
        this.emit('new_message', msg);
      }
    }, 5000);
    
    // Simulate viewer count changes
    setInterval(() => {
      this.viewerCount = Math.floor(Math.random() * 500) + 100;
    }, 10000);
  }

  updateSentiment(sentiment) {
    // Track overall viewer sentiment
    const sentimentScores = {
      'supportive': 1,
      'encouraging': 1,
      'neutral': 0,
      'analytical': 0,
      'critical': -1,
      'hostile': -2
    };
    
    this.streamMetrics.sentimentScore += sentimentScores[sentiment] || 0;
  }

  // Tool handlers
  async handleReadMessages(args) {
    const count = Math.min(args.count || 5, 10);
    const filter = args.filter || 'all';
    
    let messages = [...this.viewerMessages];
    
    // Filter messages
    if (filter === 'questions') {
      messages = messages.filter(m => m.message.includes('?'));
    } else if (filter === 'reactions') {
      messages = messages.filter(m => 
        ['supportive', 'critical', 'hostile'].includes(m.sentiment)
      );
    }
    
    // Get recent messages
    const recent = messages.slice(-count);
    
    // Format for character consumption
    const formatted = recent.map(m => ({
      from: m.username,
      message: m.message,
      sentiment: m.sentiment,
      id: m.id
    }));
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            messages: formatted,
            total_viewers: this.viewerCount,
            overall_sentiment: this.getOverallSentiment()
          }, null, 2)
        }
      ]
    };
  }

  async handleRespond(args) {
    const response = {
      character_id: this.getCurrentCharacter(),
      message: args.message,
      emotion: args.emotion,
      responding_to: args.responding_to || null,
      timestamp: Date.now()
    };
    
    // Store response
    this.characterResponses.set(Date.now(), response);
    
    // Send to stream overlay
    this.broadcastToStream({
      type: 'character_response',
      ...response
    });
    
    // Simulate viewer reactions
    this.simulateViewerReactions(response);
    
    return {
      content: [
        {
          type: 'text',
          text: `Response sent to ${this.viewerCount} viewers. Current sentiment: ${this.getOverallSentiment()}`
        }
      ]
    };
  }

  async handleCheckSentiment() {
    const sentiment = this.getOverallSentiment();
    const details = {
      overall: sentiment,
      score: this.streamMetrics.sentimentScore,
      supportive_messages: this.viewerMessages.filter(m => 
        m.sentiment === 'supportive' || m.sentiment === 'encouraging'
      ).length,
      critical_messages: this.viewerMessages.filter(m => 
        m.sentiment === 'critical' || m.sentiment === 'hostile'
      ).length,
      viewer_count: this.viewerCount
    };
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(details, null, 2)
        }
      ]
    };
  }

  async handleReadDonations() {
    const donations = [...this.donationQueue];
    this.donationQueue = []; // Clear queue after reading
    
    const total = donations.reduce((sum, d) => sum + d.amount, 0);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            donations: donations.map(d => ({
              from: d.username,
              amount: d.amount,
              message: d.message
            })),
            total_amount: total,
            can_afford: this.whatCanAfford(total)
          }, null, 2)
        }
      ]
    };
  }

  async handleThankDonor(args) {
    const thanks = {
      character_id: this.getCurrentCharacter(),
      type: 'donation_thanks',
      donor: args.donor_name,
      amount: args.amount,
      message: this.generateThankYou(args.donor_name, args.amount),
      timestamp: Date.now()
    };
    
    this.broadcastToStream(thanks);
    
    return {
      content: [
        {
          type: 'text',
          text: `Thanked ${args.donor_name} for $${args.amount} donation`
        }
      ]
    };
  }

  async handleAskForHelp(args) {
    const request = {
      character_id: this.getCurrentCharacter(),
      type: 'help_request',
      situation: args.situation,
      urgency: args.urgency,
      timestamp: Date.now()
    };
    
    this.broadcastToStream(request);
    
    // Simulate viewer responses
    setTimeout(() => {
      this.simulateHelpResponses(args.situation);
    }, 2000);
    
    return {
      content: [
        {
          type: 'text',
          text: `Asked ${this.viewerCount} viewers for help with: ${args.situation}`
        }
      ]
    };
  }

  async handleShareStory(args) {
    const story = {
      character_id: this.getCurrentCharacter(),
      type: 'personal_story',
      story: args.story,
      emotion: args.emotion,
      timestamp: Date.now()
    };
    
    this.broadcastToStream(story);
    
    // Stories increase engagement
    this.viewerCount = Math.floor(this.viewerCount * 1.2);
    
    return {
      content: [
        {
          type: 'text',
          text: `Shared story with ${this.viewerCount} viewers (engagement increased)`
        }
      ]
    };
  }

  async handleReactToComment(args) {
    const reaction = {
      character_id: this.getCurrentCharacter(),
      type: 'comment_reaction',
      comment_id: args.comment_id,
      reaction: args.reaction,
      timestamp: Date.now()
    };
    
    this.broadcastToStream(reaction);
    
    return {
      content: [
        {
          type: 'text',
          text: `Reacted with "${args.reaction}" to comment ${args.comment_id}`
        }
      ]
    };
  }

  async handleGetViewerCount() {
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            current_viewers: this.viewerCount,
            peak_viewers: Math.floor(this.viewerCount * 1.5),
            average_watch_time: '12 minutes',
            engagement_rate: this.getEngagementRate()
          }, null, 2)
        }
      ]
    };
  }

  // Helper methods
  getCurrentCharacter() {
    // Would be determined by which character is calling the tool
    return process.env.CHARACTER_ID || 'alex_chen';
  }

  getOverallSentiment() {
    const score = this.streamMetrics.sentimentScore;
    if (score > 10) return 'very_supportive';
    if (score > 0) return 'mostly_supportive';
    if (score === 0) return 'mixed';
    if (score > -10) return 'mostly_critical';
    return 'hostile';
  }

  whatCanAfford(amount) {
    // What donations enable for poor characters
    const affordances = [];
    
    if (amount >= 5) affordances.push('hot_meal');
    if (amount >= 10) affordances.push('day_of_food');
    if (amount >= 20) affordances.push('phone_bill_partial');
    if (amount >= 50) affordances.push('hostel_night');
    if (amount >= 100) affordances.push('week_of_survival');
    
    return affordances;
  }

  generateThankYou(donor, amount) {
    const character = this.getCurrentCharacter();
    
    if (character === 'alex_chen') {
      if (amount >= 50) {
        return `${donor}, you just saved me. This means I can eat for days. I'm literally crying.`;
      } else if (amount >= 20) {
        return `Thank you ${donor}. You don't know what this means. First hot meal in three days.`;
      } else {
        return `${donor}, every dollar helps. Thank you for seeing me as human.`;
      }
    } else if (character === 'madison_worthington') {
      return `Oh, ${donor}, how sweet! I'll add this to my charity fund! 💕`;
    }
    
    return `Thank you ${donor} for $${amount}`;
  }

  getEngagementRate() {
    // Calculate viewer engagement
    const messageRate = this.streamMetrics.totalMessages / Math.max(this.viewerCount, 1);
    if (messageRate > 0.1) return 'high';
    if (messageRate > 0.05) return 'medium';
    return 'low';
  }

  broadcastToStream(data) {
    // Send to stream overlay WebSocket
    if (this.chatWebSocket && this.chatWebSocket.readyState === WebSocket.OPEN) {
      this.chatWebSocket.send(JSON.stringify(data));
    }
    
    console.log('📡 Broadcast to stream:', data.type);
  }

  simulateViewerReactions(response) {
    // Viewers react to character responses
    setTimeout(() => {
      if (response.emotion === 'desperate') {
        this.viewerMessages.push({
          id: `reaction_${Date.now()}`,
          username: 'empathetic_viewer',
          message: 'This is heartbreaking. How is this America?',
          sentiment: 'supportive',
          timestamp: Date.now()
        });
      } else if (response.emotion === 'grateful') {
        this.viewerMessages.push({
          id: `reaction_${Date.now()}`,
          username: 'inspired_viewer',
          message: 'Your strength is incredible. Keep going!',
          sentiment: 'encouraging',
          timestamp: Date.now()
        });
      }
    }, 1000);
  }

  simulateHelpResponses(situation) {
    // Viewers respond to help requests
    if (situation.includes('food')) {
      this.donationQueue.push({
        id: `help_donation_${Date.now()}`,
        type: 'donation',
        username: 'meal_provider',
        amount: 15,
        message: 'For a hot meal. No one should be hungry.',
        timestamp: Date.now()
      });
    }
    
    this.viewerMessages.push({
      id: `help_msg_${Date.now()}`,
      username: 'resource_sharer',
      message: `Try the food bank on 5th street, open until 6pm`,
      sentiment: 'supportive',
      timestamp: Date.now()
    });
  }
}

// Main execution
async function main() {
  const server = new ViewerCommunicationServer();
  await server.initialize();
  
  console.log('🎭 MCP Viewer Communication Server running');
  console.log('Characters can now:');
  console.log('  • Read viewer messages and reactions');
  console.log('  • Respond directly to stream audience');
  console.log('  • Check viewer sentiment');
  console.log('  • Receive and acknowledge donations');
  console.log('  • Ask viewers for help or advice');
  console.log('  • Share personal stories');
  console.log('  • React to specific comments\n');
  
  // Keep process alive
  process.stdin.resume();
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = { ViewerCommunicationServer };