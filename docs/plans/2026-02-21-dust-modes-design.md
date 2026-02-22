# Dust Modes Design

## Overview
Replace the single dust behavior with 5 selectable modes via tabs in the Dust section. Only one mode active at a time.

## Modes

### Classic
Current behavior. Particles spawn at motion edges, fly off with turbulence/branching.
Controls: Speed, Density, Spread, Sensitivity, Color From/To

### Trails
Particles spawn at motion edges and travel in the direction of movement. Motion vector computed per edge block: direction points from unchanged neighbor toward the changed region.
Controls: Trail Length (lifetime), Speed, Density, Color From/To

### Glow
No particles. Heat buffer (Float32Array, same grid as change detection) accumulates where motion detected, decays over time. Rendered as semi-transparent color overlay.
Controls: Intensity, Decay, Color From/To

### Outline
Particles spawn at motion edges with velocity tangent to the edge contour (perpendicular to edge normal, consistently rotated). They skate along silhouette boundaries.
Controls: Speed, Density, Color From/To

### Eruptions
Tracks total changed area per frame. When change rate spikes above threshold, spawns large burst from center of changed region. Quiet during slow scenes, explosive during transitions.
Controls: Threshold, Burst Size, Color From/To

## UI
```
[x] Dust
  [Classic] [Trails] [Glow] [Outline] [Eruptions]
  (mode-specific controls)
```

## Config Serialization
- `dm`: dust mode string
- Classic: existing keys (ds, dd, dp, dx, dc1, dc2)
- Trails: tl, ts, td, tc1, tc2
- Glow: gi, gd, gc1, gc2
- Outline: os, od, oc1, oc2
- Eruptions: et, eb, ec1, ec2
