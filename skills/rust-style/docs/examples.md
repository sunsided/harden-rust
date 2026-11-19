# Before / after

## Doc comments (rule 1)

Before:

```rust
pub struct Body {
    pub pos: Vec2,
    pub vel: Vec2,
    mass: f32,
}

fn clamp_speed(v: Vec2, max: f32) -> Vec2 { /* ... */ }
```

After:

```rust
/// A rigid body tracked by the physics step.
///
/// Bodies are integrated with semi-implicit Euler; see [`World::integrate`].
pub struct Body {
    /// Center of mass in world units (1 unit = 1 meter).
    pub pos: Vec2,

    /// Linear velocity in meters per second.
    pub vel: Vec2,

    /// Mass in kilograms. Always positive; zero-mass bodies are rejected by [`Body::new`].
    mass: f32,
}

/// Scales `v` down so its length does not exceed `max`, keeping its direction.
///
/// Returns `v` unchanged when it is already within the limit. `max` must be non-negative.
fn clamp_speed(v: Vec2, max: f32) -> Vec2 { /* ... */ }
```

Blank lines between documented fields are optional. Use them when the docs span several lines.

## No mod.rs (rule 2)

```text
Before                       After
src/net/mod.rs               src/net.rs
src/net/client.rs            src/net/client.rs
src/net/server.rs            src/net/server.rs
tests/common/mod.rs          tests/it/main.rs     (mod common; mod api;)
tests/api.rs                 tests/it/common.rs
                             tests/it/api.rs
```

## Separator comments (rule 3)

Before (`src/game.rs`):

```rust
// ---------------- Input ----------------
fn read_input() { /* ... */ }
fn map_keys() { /* ... */ }

// ---------------- Rendering ----------------
fn draw_board() { /* ... */ }
fn draw_hud() { /* ... */ }
```

After:

```rust
// src/game.rs
//! Game loop and top-level state.

mod input;
mod render;
```

```rust
// src/game/input.rs
//! Keyboard and gamepad input, mapped to game actions.

/// Polls the platform for pending input events.
fn read_input() { /* ... */ }
```

## Blank lines (rule 4)

Before:

```rust
fn spawn_wave(&mut self, wave: u32) -> usize {
    let count = 5 + wave as usize * 2;
    let speed = 1.0 + wave as f32 * 0.1;
    if self.enemies.len() + count > MAX_ENEMIES {
        return 0;
    }
    for i in 0..count {
        let pos = self.spawn_point(i);
        self.enemies.push(Enemy::new(pos, speed));
    }
    self.wave = wave;
    count
}
```

After:

```rust
/// Spawns the enemies of `wave` and returns how many were spawned.
///
/// Spawns nothing (and returns 0) when the wave would exceed [`MAX_ENEMIES`].
fn spawn_wave(&mut self, wave: u32) -> usize {
    let count = 5 + usize::try_from(wave).expect("wave fits in usize") * 2;
    let speed = 1.0 + f32::from(u16::try_from(wave).unwrap_or(u16::MAX)) * 0.1;

    if self.enemies.len() + count > MAX_ENEMIES {
        return 0;
    }

    for i in 0..count {
        let pos = self.spawn_point(i);
        self.enemies.push(Enemy::new(pos, speed));
    }

    self.wave = wave;
    count
}
```

## Helper extraction (rule 5)

Before:

```rust
fn update(&mut self, dt: f32) {
    // apply gravity and integrate
    for b in &mut self.bodies {
        b.vel += GRAVITY * dt;
        b.pos += b.vel * dt;
    }
    // collide with floor
    for b in &mut self.bodies {
        if b.pos.y < 0.0 {
            b.pos.y = 0.0;
            if b.vel.y < 0.0 {
                b.vel.y = -b.vel.y * RESTITUTION;
            }
        }
    }
    // despawn far away bodies
    self.bodies.retain(|b| b.pos.length() < WORLD_RADIUS);
}
```

After:

```rust
/// Advances the world by `dt` seconds.
fn update(&mut self, dt: f32) {
    self.integrate(dt);
    self.resolve_floor_collisions();
    self.despawn_escaped();
}

/// Applies gravity and moves every body by its velocity (semi-implicit Euler).
fn integrate(&mut self, dt: f32) {
    for body in &mut self.bodies {
        body.vel += GRAVITY * dt;
        body.pos += body.vel * dt;
    }
}

/// Pushes bodies below the floor back onto it and bounces them with [`RESTITUTION`].
fn resolve_floor_collisions(&mut self) {
    for body in self.bodies.iter_mut().filter(|b| b.pos.y < 0.0) {
        body.pos.y = 0.0;
        body.vel.y = bounce(body.vel.y);
    }
}

/// Reflects a downward vertical velocity, losing energy; upward velocities pass through.
fn bounce(vy: f32) -> f32 {
    if vy < 0.0 { -vy * RESTITUTION } else { vy }
}

/// Removes bodies that left the simulated area.
fn despawn_escaped(&mut self) {
    self.bodies.retain(|b| b.pos.length() < WORLD_RADIUS);
}
```

## Suppression (rule 6)

```rust
// Wrong
#[allow(clippy::cast_possible_truncation)]

// Right: scoped, justified, and reports when it becomes stale
#[expect(clippy::cast_possible_truncation, reason = "tile index is bounded by GRID_SIZE (64)")]
fn tile_index(x: usize) -> u8 { x as u8 }
```
