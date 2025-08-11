#!/usr/bin/env node
/**
 * Multi-Character Orchestrator
 * Manages multiple characters in the same world, handling encounters and interactions
 */

const { Client } = require('@modelcontextprotocol/sdk/client/index.js');
const WebSocket = require('ws');
const EventEmitter = require('events');

class MultiCharacterWorld extends EventEmitter {
  constructor(config) {
    super();
    this.config = config;
    this.characters = new Map();
    this.locations = new Map();
    this.encounters = new Map();
    this.worldClock = new Date();
    this.spatialGrid = {};
    
    // Track character positions and states
    this.characterStates = new Map();
    
    // WebSocket for AI decisions
    this.aiWebSocket = null;
    
    // Unreal Engine connection
    this.unrealConnections = new Map();
  }

  async initialize() {
    console.log('🌍 Initializing Multi-Character World...\n');
    
    // Connect to AI decision service
    if (this.config.aiWebSocketUrl) {
      await this.connectToAI();
    }
    
    // Initialize world locations
    this.initializeLocations();
    
    // Spawn initial characters
    await this.spawnCharacters(this.config.initialCharacters);
    
    console.log('✅ World initialized with', this.characters.size, 'characters\n');
  }

  initializeLocations() {
    // Define world locations and their properties
    const locations = [
      {
        id: 'public_library',
        name: 'Public Library',
        type: 'public',
        capacity: 50,
        resources: ['wifi', 'power_outlets', 'bathrooms', 'water_fountain'],
        restrictions: {
          poor: { time_limit: 120, security_scrutiny: 'high' },
          wealthy: { time_limit: null, security_scrutiny: 'none' }
        },
        coordinates: { x: 100, y: 200, z: 0 }
      },
      {
        id: 'coffee_shop',
        name: 'Artisan Coffee Shop',
        type: 'commercial',
        capacity: 30,
        resources: ['wifi', 'food', 'drinks', 'seating'],
        restrictions: {
          poor: { access: 'employee_only', must_purchase: true },
          wealthy: { access: 'customer', reserved_seating: true }
        },
        coordinates: { x: 300, y: 200, z: 0 }
      },
      {
        id: 'food_bank',
        name: 'Community Food Bank',
        type: 'charity',
        capacity: 100,
        resources: ['free_food', 'social_services'],
        restrictions: {
          poor: { access: 'full', wait_time: 45 },
          wealthy: { access: 'volunteer_only', photo_op: true }
        },
        coordinates: { x: 150, y: 400, z: 0 }
      },
      {
        id: 'luxury_apartment',
        name: 'The Heights Luxury Apartments',
        type: 'residential',
        capacity: 200,
        resources: ['private_gym', 'rooftop_pool', 'concierge'],
        restrictions: {
          poor: { access: 'denied', security: 'will_call_police' },
          wealthy: { access: 'resident', amenities: 'all' }
        },
        coordinates: { x: 500, y: 500, z: 100 }
      }
    ];
    
    locations.forEach(loc => {
      this.locations.set(loc.id, loc);
      this.spatialGrid[loc.id] = new Set();
    });
  }

  async spawnCharacters(characterList) {
    for (const charConfig of characterList) {
      const character = {
        id: charConfig.id,
        name: charConfig.name,
        economicTier: charConfig.economicTier,
        location: charConfig.startLocation,
        state: {
          animation: 'idle',
          needs: charConfig.initialNeeds || {
            hunger: 50,
            thirst: 50,
            exhaustion: 30,
            stress: charConfig.economicTier === 'poor' ? 70 : 20
          },
          money: charConfig.money,
          inventory: charConfig.inventory || []
        },
        perceptionRadius: charConfig.economicTier === 'poor' ? 20 : 50, // Poor people forced to focus on immediate survival
        lastUpdate: Date.now()
      };
      
      this.characters.set(charConfig.id, character);
      this.characterStates.set(charConfig.id, character.state);
      
      // Place character in spatial grid
      if (this.spatialGrid[character.location]) {
        this.spatialGrid[character.location].add(charConfig.id);
      }
      
      console.log(`✓ Spawned ${character.name} at ${character.location}`);
    }
  }

  async connectToAI() {
    return new Promise((resolve) => {
      console.log('🤖 Connecting to AI decision service...');
      
      this.aiWebSocket = new WebSocket(this.config.aiWebSocketUrl);
      
      this.aiWebSocket.on('open', () => {
        console.log('   ✓ Connected to AI service\n');
        resolve();
      });
      
      this.aiWebSocket.on('message', (data) => {
        this.handleAIDecision(JSON.parse(data));
      });
    });
  }

  // World tick - update all characters and check for encounters
  async worldTick() {
    const tickStart = Date.now();
    
    // Update world clock
    this.worldClock = new Date();
    
    // Generate perception for each character
    for (const [charId, character] of this.characters) {
      const perception = this.generatePerception(charId);
      character.currentPerception = perception;
      
      // Check for encounters
      const nearbyCharacters = this.getNearbyCharacters(charId);
      if (nearbyCharacters.length > 0) {
        this.checkForEncounters(charId, nearbyCharacters);
      }
      
      // Send perception to AI for decision
      if (this.aiWebSocket && this.aiWebSocket.readyState === WebSocket.OPEN) {
        this.aiWebSocket.send(JSON.stringify({
          type: 'perception_update',
          character_id: charId,
          perception: perception,
          timestamp: this.worldClock.toISOString()
        }));
      }
    }
    
    // Process active encounters
    this.processEncounters();
    
    // Update Unreal with world state
    this.updateUnrealWorld();
    
    const tickDuration = Date.now() - tickStart;
    this.emit('world_tick', { duration: tickDuration, time: this.worldClock });
  }

  generatePerception(characterId) {
    const character = this.characters.get(characterId);
    const location = this.locations.get(character.location);
    
    // What can this character see based on their state?
    const perception = {
      location: {
        id: location.id,
        name: location.name,
        description: this.getLocationDescription(location, character.economicTier),
        available_resources: this.getAccessibleResources(location, character.economicTier),
        atmosphere: this.getAtmosphere(location, character.economicTier)
      },
      visible_characters: [],
      available_actions: [],
      threats: [],
      opportunities: [],
      sensory: {
        sounds: this.getAmbientSounds(location),
        smells: this.getAmbientSmells(location),
        temperature: this.getTemperature(location),
        lighting: this.getLighting(location, this.worldClock.getHours())
      }
    };
    
    // Get visible characters
    const nearbyChars = this.getNearbyCharacters(characterId);
    for (const otherId of nearbyChars) {
      const other = this.characters.get(otherId);
      perception.visible_characters.push({
        id: otherId,
        appearance: this.getCharacterAppearance(other),
        activity: other.state.animation,
        distance: this.calculateDistance(character, other),
        facing: this.calculateFacing(character, other),
        economicIndicators: this.getEconomicIndicators(other)
      });
    }
    
    // Determine available actions based on context
    perception.available_actions = this.getAvailableActions(character, location, nearbyChars);
    
    // Identify threats (for poor characters)
    if (character.economicTier === 'poor') {
      perception.threats = this.identifyThreats(character, location, nearbyChars);
    }
    
    // Identify opportunities
    perception.opportunities = this.identifyOpportunities(character, location, nearbyChars);
    
    return perception;
  }

  getNearbyCharacters(characterId) {
    const character = this.characters.get(characterId);
    const nearby = [];
    
    // Get all characters in same location
    const charsInLocation = this.spatialGrid[character.location] || new Set();
    
    for (const otherId of charsInLocation) {
      if (otherId !== characterId) {
        const other = this.characters.get(otherId);
        const distance = this.calculateDistance(character, other);
        
        // Check if within perception radius
        if (distance <= character.perceptionRadius) {
          nearby.push(otherId);
        }
      }
    }
    
    return nearby;
  }

  checkForEncounters(characterId, nearbyCharacters) {
    const character = this.characters.get(characterId);
    
    for (const otherId of nearbyCharacters) {
      const other = this.characters.get(otherId);
      const distance = this.calculateDistance(character, other);
      
      // Close enough for interaction?
      if (distance < 5) {
        const encounterId = this.createEncounterId(characterId, otherId);
        
        if (!this.encounters.has(encounterId)) {
          // New encounter!
          const encounter = {
            id: encounterId,
            participants: [characterId, otherId],
            type: this.determineEncounterType(character, other),
            location: character.location,
            startTime: this.worldClock,
            phase: 'initial',
            interactions: []
          };
          
          this.encounters.set(encounterId, encounter);
          this.emit('encounter_started', encounter);
          
          console.log(`\n🤝 ENCOUNTER: ${character.name} meets ${other.name}`);
          console.log(`   Type: ${encounter.type}`);
        }
      }
    }
  }

  determineEncounterType(char1, char2) {
    const tier1 = char1.economicTier;
    const tier2 = char2.economicTier;
    
    if (tier1 === 'poor' && tier2 === 'poor') {
      return 'solidarity';
    } else if (tier1 === 'poor' && tier2 === 'wealthy') {
      return 'class_collision';
    } else if (tier1 === 'wealthy' && tier2 === 'poor') {
      return 'class_collision';
    } else if (tier1 === 'wealthy' && tier2 === 'wealthy') {
      return 'networking';
    } else {
      return 'neutral';
    }
  }

  processEncounters() {
    for (const [encounterId, encounter] of this.encounters) {
      // Generate interactions based on encounter type
      const interactions = this.generateInteractions(encounter);
      
      for (const interaction of interactions) {
        // Send to Unreal for animation
        this.sendToUnreal(interaction.character, {
          type: 'interaction',
          action: interaction.action,
          target: interaction.target,
          animation: interaction.animation,
          dialogue: interaction.dialogue
        });
        
        // Update character states
        const character = this.characters.get(interaction.character);
        if (character) {
          this.updateCharacterState(character, interaction);
        }
      }
      
      // Check if encounter should end
      if (this.shouldEndEncounter(encounter)) {
        this.encounters.delete(encounterId);
        this.emit('encounter_ended', encounter);
      }
    }
  }

  generateInteractions(encounter) {
    const interactions = [];
    
    switch(encounter.type) {
      case 'class_collision':
        // Wealthy character shows disgust/avoidance
        interactions.push({
          character: encounter.participants.find(p => 
            this.characters.get(p).economicTier === 'wealthy'
          ),
          action: 'avoid',
          target: encounter.participants.find(p => 
            this.characters.get(p).economicTier === 'poor'
          ),
          animation: 'disgusted_look_away',
          dialogue: null // Internal disgust, no verbal interaction
        });
        
        // Poor character feels shame
        interactions.push({
          character: encounter.participants.find(p => 
            this.characters.get(p).economicTier === 'poor'
          ),
          action: 'shame_response',
          target: 'self',
          animation: 'hunch_shoulders',
          dialogue: null
        });
        break;
        
      case 'solidarity':
        // Poor characters help each other
        const [char1, char2] = encounter.participants;
        
        // Check if one has food to share
        const character1 = this.characters.get(char1);
        const character2 = this.characters.get(char2);
        
        if (character1.state.inventory.includes('food') && character2.state.needs.hunger > 70) {
          interactions.push({
            character: char1,
            action: 'share_food',
            target: char2,
            animation: 'give_item',
            dialogue: "I have extra. Take this."
          });
        }
        
        // Share survival information
        interactions.push({
          character: char2,
          action: 'share_info',
          target: char1,
          animation: 'whisper',
          dialogue: "Security is cracking down. Be careful."
        });
        break;
        
      case 'networking':
        // Wealthy characters network
        interactions.push({
          character: encounter.participants[0],
          action: 'network',
          target: encounter.participants[1],
          animation: 'confident_handshake',
          dialogue: "Let's discuss that investment opportunity."
        });
        break;
    }
    
    return interactions;
  }

  updateCharacterState(character, interaction) {
    switch(interaction.action) {
      case 'avoid':
        character.state.stress = Math.max(0, character.state.stress - 5); // Less stress avoiding "undesirables"
        break;
      case 'shame_response':
        character.state.stress = Math.min(100, character.state.stress + 10);
        break;
      case 'share_food':
        const foodIndex = character.state.inventory.indexOf('food');
        if (foodIndex > -1) {
          character.state.inventory.splice(foodIndex, 1);
        }
        break;
      case 'network':
        character.state.money *= 1.01; // Networking leads to more wealth
        break;
    }
  }

  sendToUnreal(characterId, command) {
    const unrealConnection = this.unrealConnections.get(characterId);
    if (unrealConnection) {
      unrealConnection.send(JSON.stringify({
        character_id: characterId,
        ...command,
        timestamp: this.worldClock.toISOString()
      }));
    }
  }

  updateUnrealWorld() {
    // Send complete world state to Unreal
    const worldState = {
      type: 'world_update',
      time: this.worldClock.toISOString(),
      characters: Array.from(this.characters.entries()).map(([id, char]) => ({
        id: id,
        location: char.location,
        position: this.getCharacterPosition(char),
        state: char.state,
        perception: char.currentPerception
      })),
      encounters: Array.from(this.encounters.values()),
      locations: Array.from(this.locations.values())
    };
    
    // Broadcast to all Unreal connections
    for (const connection of this.unrealConnections.values()) {
      connection.send(JSON.stringify(worldState));
    }
  }

  // Helper methods
  calculateDistance(char1, char2) {
    // Simple distance calculation (would be more complex in real 3D space)
    return Math.random() * 50; // Placeholder
  }

  calculateFacing(char1, char2) {
    // Are characters facing each other?
    return Math.random() > 0.5 ? 'toward' : 'away';
  }

  createEncounterId(id1, id2) {
    return [id1, id2].sort().join('_');
  }

  shouldEndEncounter(encounter) {
    // End encounter after certain duration or if characters move apart
    const duration = this.worldClock - encounter.startTime;
    return duration > 30000; // 30 seconds
  }

  getCharacterAppearance(character) {
    const appearances = {
      poor: 'Worn clothes, exhausted posture, carrying old backpack',
      middle: 'Business casual, tired but presentable',
      wealthy: 'Designer clothes, confident posture, latest gadgets',
      ultra_wealthy: 'Couture fashion, oblivious expression, personal assistant nearby'
    };
    
    return appearances[character.economicTier] || 'Average appearance';
  }

  getEconomicIndicators(character) {
    const indicators = [];
    
    if (character.economicTier === 'poor') {
      indicators.push('worn_shoes', 'old_phone', 'reusable_water_bottle');
    } else if (character.economicTier === 'wealthy') {
      indicators.push('designer_watch', 'latest_iphone', 'artisan_coffee');
    } else if (character.economicTier === 'ultra_wealthy') {
      indicators.push('personal_assistant', 'multiple_phones', 'ignoring_prices');
    }
    
    return indicators;
  }

  identifyThreats(character, location, nearbyCharacters) {
    const threats = [];
    
    if (character.economicTier === 'poor') {
      // Security is always a threat
      if (location.restrictions.poor.security_scrutiny === 'high') {
        threats.push({
          type: 'security',
          severity: 'high',
          description: 'Security guard approaching'
        });
      }
      
      // Time limits
      if (location.restrictions.poor.time_limit) {
        threats.push({
          type: 'eviction',
          severity: 'medium',
          description: `${location.restrictions.poor.time_limit} minute limit`
        });
      }
      
      // Wealthy people might complain
      const wealthyNearby = nearbyCharacters.filter(id => 
        this.characters.get(id).economicTier === 'wealthy'
      );
      if (wealthyNearby.length > 0) {
        threats.push({
          type: 'complaint',
          severity: 'medium',
          description: 'Wealthy person might complain about you'
        });
      }
    }
    
    return threats;
  }

  identifyOpportunities(character, location, nearbyCharacters) {
    const opportunities = [];
    
    if (character.economicTier === 'poor') {
      // Other poor people might help
      const poorNearby = nearbyCharacters.filter(id => 
        this.characters.get(id).economicTier === 'poor'
      );
      if (poorNearby.length > 0) {
        opportunities.push({
          type: 'solidarity',
          description: 'Another struggling person might share resources'
        });
      }
      
      // Available resources
      if (location.resources.includes('wifi')) {
        opportunities.push({
          type: 'resource',
          description: 'Free wifi to submit gig work'
        });
      }
    }
    
    return opportunities;
  }

  getLocationDescription(location, economicTier) {
    const descriptions = {
      public_library: {
        poor: 'Harsh fluorescent lights. Security watches. Other homeless people guard outlets.',
        wealthy: 'Quiet study space with helpful staff and available resources.'
      },
      coffee_shop: {
        poor: 'Behind the counter. Burns from steam. Manager watching every move.',
        wealthy: 'Cozy atmosphere. Barista knows your name. Perfect for meetings.'
      }
    };
    
    return descriptions[location.id]?.[economicTier] || 'A place in the city';
  }

  getAccessibleResources(location, economicTier) {
    const resources = [...location.resources];
    const restrictions = location.restrictions[economicTier];
    
    if (restrictions.access === 'denied') {
      return [];
    }
    
    if (restrictions.must_purchase) {
      return resources.filter(r => r === 'bathrooms' || r === 'wifi');
    }
    
    return resources;
  }

  getAvailableActions(character, location, nearbyCharacters) {
    const actions = ['look_around', 'check_phone', 'wait'];
    
    if (character.economicTier === 'poor') {
      actions.push('look_for_outlet', 'avoid_security', 'make_yourself_small');
      
      if (location.resources.includes('water_fountain')) {
        actions.push('drink_water');
      }
      
      if (nearbyCharacters.some(id => 
        this.characters.get(id).economicTier === 'poor'
      )) {
        actions.push('approach_for_help');
      }
    } else if (character.economicTier === 'wealthy') {
      actions.push('order_coffee', 'take_call', 'check_stocks', 'network');
      
      if (nearbyCharacters.some(id => 
        this.characters.get(id).economicTier === 'poor'
      )) {
        actions.push('avoid_eye_contact', 'move_away');
      }
    }
    
    return actions;
  }

  // Environmental details
  getAtmosphere(location, economicTier) {
    if (economicTier === 'poor') {
      return 'hostile_scrutinized';
    } else if (economicTier === 'wealthy') {
      return 'comfortable_welcomed';
    }
    return 'neutral';
  }

  getAmbientSounds(location) {
    const sounds = {
      public_library: ['keyboard_typing', 'whispers', 'page_turning', 'footsteps'],
      coffee_shop: ['espresso_machine', 'milk_steaming', 'jazz_music', 'chatter'],
      food_bank: ['shuffling_feet', 'coughing', 'volunteer_instructions', 'bags_rustling']
    };
    
    return sounds[location.id] || ['ambient_city'];
  }

  getAmbientSmells(location) {
    const smells = {
      public_library: ['old_books', 'floor_cleaner', 'unwashed_clothes'],
      coffee_shop: ['fresh_coffee', 'baked_goods', 'expensive_perfume'],
      food_bank: ['disinfectant', 'old_vegetables', 'desperation']
    };
    
    return smells[location.id] || ['city_air'];
  }

  getTemperature(location) {
    // Poor people experience worse climate control
    return location.type === 'public' ? 'too_cold' : 'comfortable';
  }

  getLighting(location, hour) {
    if (hour < 6 || hour > 20) {
      return 'dim_artificial';
    }
    return location.type === 'public' ? 'harsh_fluorescent' : 'warm_natural';
  }

  getCharacterPosition(character) {
    // Would integrate with actual Unreal position data
    return {
      x: Math.random() * 1000,
      y: Math.random() * 1000,
      z: 0
    };
  }
}

// Main execution
async function main() {
  const config = {
    aiWebSocketUrl: process.env.AI_WEBSOCKET_URL || 'wss://localhost:8080',
    initialCharacters: [
      {
        id: 'alex_chen',
        name: 'Alex Chen',
        economicTier: 'poor',
        startLocation: 'public_library',
        money: 53.09,
        inventory: ['old_laptop', 'water_bottle'],
        initialNeeds: { hunger: 75, thirst: 40, exhaustion: 85, stress: 90 }
      },
      {
        id: 'madison_worthington',
        name: 'Madison Worthington',
        economicTier: 'ultra_wealthy',
        startLocation: 'public_library',
        money: 25000000,
        inventory: ['iphone_15_pro', 'designer_bag', 'credit_cards'],
        initialNeeds: { hunger: 10, thirst: 0, exhaustion: 0, stress: 5 }
      },
      {
        id: 'jamie_rodriguez',
        name: 'Jamie Rodriguez',
        economicTier: 'poor',
        startLocation: 'coffee_shop',
        money: 43,
        inventory: ['apron', 'name_tag', 'half_sandwich'],
        initialNeeds: { hunger: 60, thirst: 30, exhaustion: 70, stress: 75 }
      }
    ]
  };
  
  const world = new MultiCharacterWorld(config);
  
  await world.initialize();
  
  // Start world simulation
  console.log('🎮 Starting world simulation...\n');
  
  // Run world ticks
  setInterval(() => {
    world.worldTick();
  }, 1000); // Tick every second
  
  // Listen for events
  world.on('encounter_started', (encounter) => {
    console.log(`\n🤝 NEW ENCOUNTER: ${encounter.type}`);
    console.log(`   Participants: ${encounter.participants.join(', ')}`);
    console.log(`   Location: ${encounter.location}`);
  });
  
  world.on('encounter_ended', (encounter) => {
    console.log(`\n👋 ENCOUNTER ENDED: ${encounter.id}`);
  });
  
  world.on('world_tick', (data) => {
    if (data.time.getSeconds() % 10 === 0) {
      console.log(`⏰ World time: ${data.time.toLocaleTimeString()}`);
    }
  });
}

// Run if executed directly
if (require.main === module) {
  main().catch(console.error);
}

module.exports = { MultiCharacterWorld };