# Particle System Implementation Plan

## Overview

Implementation of a Ursina-based particle system for KotOR effects, based on reone's architecture and MDL emitter data.

## Components

### 1. Particle Class

```python
class Particle:
    """Individual particle instance."""
    def __init__(self):
        self.position: Vec3
        self.velocity: Vec3
        self.direction: Vec3
        self.color: Vec4
        self.size: Vec2
        self.lifetime: float
        self.alpha: float
        self.frame: int
        self.anim_length: float
```

### 2. Emitter Class

```python
class ParticleEmitter:
    """Manages particle spawning and lifecycle."""
    def __init__(self):
        self.birth_rate: float
        self.life_expectancy: float
        self.particle_size: tuple[float, float, float]  # start, mid, end
        self.particle_color: tuple[Vec3, Vec3, Vec3]    # start, mid, end
        self.particle_alpha: tuple[float, float, float] # start, mid, end
        self.velocity: float
        self.spread: float
        self.gravity: float
        self.particles: list[Particle]
```

## Implementation Phases

### Phase 1: Basic Structure

1. Create particle and emitter classes
2. Set up particle pool system
3. Implement basic particle lifecycle
4. Add particle property interpolation

### Phase 2: MDL Integration

1. Update MDLProcessor._process_emitter
2. Convert MDL emitter properties
3. Handle emitter controllers
4. Set up particle textures

### Phase 3: Rendering

1. Create particle geometry
2. Set up material system
3. Implement particle shaders
4. Add render sorting

### Phase 4: Effects

1. Add particle physics
2. Implement special effects (lightning, etc)
3. Add particle collisions
4. Optimize performance

## MDL Emitter Properties

Properties to handle from MDL format:

- Dead space
- Blast radius/length
- Branch count
- Control point smoothing
- Grid settings
- Update/render/blend modes
- Texture settings
- Animation properties

## Technical Details

### Particle Updates

```python
def update_particle(self, dt: float):
    """Update single particle state."""
    # Update position
    self.position += self.velocity * dt
    
    # Apply gravity
    self.velocity.z -= self.gravity * dt
    
    # Update lifetime
    self.lifetime -= dt
    
    # Interpolate properties
    self.update_properties(dt)
```

### Emitter Updates

```python
def update(self, dt: float):
    """Update emitter and particles."""
    # Spawn new particles
    self.spawn_particles(dt)
    
    # Update existing particles
    self.update_particles(dt)
    
    # Remove expired particles
    self.remove_expired()
```

### Rendering Pipeline

1. Sort particles by distance
2. Update particle geometry
3. Apply particle materials
4. Handle transparency
5. Render particles

## Integration with Ursina

### Scene Graph

```
Scene Root
└── Emitter Node
    ├── Particle 1
    ├── Particle 2
    └── Particle N
```

### Rendering System

- Use GeomParticles for efficient rendering
- Implement particle shaders
- Handle particle sorting
- Support multiple blend modes

## Performance Considerations

1. Particle Pool

- Pre-allocate particles
- Reuse particle objects
- Manage memory efficiently

2. Rendering Optimization

- Batch particle rendering
- Use instancing where possible
- Implement LOD system

3. Update Optimization

- Spatial partitioning
- Culling inactive particles
- Efficient property updates

## Testing Plan

1. Unit Tests

- Particle lifecycle
- Property interpolation
- Physics calculations

2. Integration Tests

- MDL conversion
- Emitter behavior
- Rendering pipeline

3. Performance Tests

- Particle count limits
- Memory usage
- Frame rate impact

## Next Steps

1. Initial Implementation

- [ ] Create basic particle class
- [ ] Implement emitter system
- [ ] Set up particle pool
- [ ] Add basic rendering

2. MDL Integration

- [ ] Update MDLProcessor
- [ ] Convert emitter properties
- [ ] Handle controllers
- [ ] Test with sample MDL files

3. Advanced Features

- [ ] Add physics system
- [ ] Implement special effects
- [ ] Optimize performance
- [ ] Add full MDL support
