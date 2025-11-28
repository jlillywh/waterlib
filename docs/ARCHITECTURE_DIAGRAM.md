# Waterlib Architecture Diagrams

Visual overview of waterlib architecture.

---

## System Architecture Overview

```mermaid
graph TB
    subgraph "User Layer"
        YAML[YAML Model Definition]
        Python[Python API]
    end

    subgraph "Core Framework"
        Loader[Model Loader]
        Model[Model Container]
        Simulation[Simulation Engine]
        Results[Results Handler]
    end

    subgraph "Component Layer"
        Catchment[Catchment Component]
        Reservoir[Reservoir Component]
        Pump[Pump Component]
        Demand[Demand Component]
    end

    subgraph "Kernel Layer"
        Snow17[Snow17 Kernel]
        AWBM[AWBM Kernel]
        Weir[Weir Kernel]
        ET[Hargreaves ET Kernel]
    end

    YAML --> Loader
    Python --> Loader
    Loader --> Model
    Model --> Simulation
    Simulation --> Results

    Simulation --> Catchment
    Simulation --> Reservoir
    Simulation --> Pump
    Simulation --> Demand

    Catchment --> Snow17
    Catchment --> AWBM
    Reservoir --> Weir
    Catchment --> ET

    style YAML fill:#e1f5ff
    style Python fill:#e1f5ff
    style Loader fill:#fff4e1
    style Model fill:#fff4e1
    style Simulation fill:#fff4e1
    style Results fill:#fff4e1
    style Catchment fill:#e8f5e9
    style Reservoir fill:#e8f5e9
    style Pump fill:#e8f5e9
    style Demand fill:#e8f5e9
    style Snow17 fill:#f3e5f5
    style AWBM fill:#f3e5f5
    style Weir fill:#f3e5f5
    style ET fill:#f3e5f5
```

---

## Dependency Flow

```mermaid
graph LR
    YAML[YAML Configuration] --> Components[Components Layer]
    Components --> Kernels[Kernels Layer]

    style YAML fill:#e1f5ff
    style Components fill:#e8f5e9
    style Kernels fill:#f3e5f5
```

**Key Principle:** Dependencies flow one direction. Kernels never import components.

---

## Kernel Organization

```mermaid
graph TB
    subgraph "waterlib/kernels/"
        subgraph "hydrology/"
            Snow17[snow17.py<br/>Snow accumulation/melt]
            AWBM[awbm.py<br/>Rainfall-runoff]
            Runoff[runoff.py<br/>Runoff utilities]
        end

        subgraph "hydraulics/"
            Weir[weir.py<br/>Weir equations]
            Spillway[spillway.py<br/>Spillway calcs]
        end

        subgraph "climate/"
            ET[et.py<br/>ET methods]
            WGEN[wgen.py<br/>Weather generator]
        end
    end

    style Snow17 fill:#f3e5f5
    style AWBM fill:#f3e5f5
    style Runoff fill:#f3e5f5
    style Weir fill:#f3e5f5
    style Spillway fill:#f3e5f5
    style ET fill:#f3e5f5
    style WGEN fill:#f3e5f5
```

---

## Component-Kernel Relationship

```mermaid
graph TB
    subgraph "Catchment Component"
        CatchInit[Initialize<br/>- Create kernel params<br/>- Initialize kernel states]
        CatchStep[step&#40;&#41;<br/>- Get inputs<br/>- Call Snow17 kernel<br/>- Call AWBM kernel<br/>- Package outputs]
    end

    subgraph "Snow17 Kernel"
        Snow17Func[snow17_step&#40;&#41;<br/>Pure function<br/>inputs → outputs]
    end

    subgraph "AWBM Kernel"
        AWBMFunc[awbm_step&#40;&#41;<br/>Pure function<br/>inputs → outputs]
    end

    CatchInit -.creates.-> Snow17Params[Snow17Params]
    CatchInit -.creates.-> AWBMParams[AWBMParams]
    CatchStep --> Snow17Func
    CatchStep --> AWBMFunc
    Snow17Func -.uses.-> Snow17Params
    AWBMFunc -.uses.-> AWBMParams

    style CatchInit fill:#e8f5e9
    style CatchStep fill:#e8f5e9
    style Snow17Func fill:#f3e5f5
    style AWBMFunc fill:#f3e5f5
    style Snow17Params fill:#fff4e1
    style AWBMParams fill:#fff4e1
```

---

## Kernel Function Pattern

```mermaid
graph LR
    Inputs[Inputs<br/>dataclass] --> Kernel[kernel_step&#40;&#41;<br/>Pure Function]
    Params[Params<br/>dataclass] --> Kernel
    StateIn[State<br/>dataclass] --> Kernel
    Kernel --> StateOut[New State<br/>dataclass]
    Kernel --> Outputs[Outputs<br/>dataclass]

    style Inputs fill:#e1f5ff
    style Params fill:#fff4e1
    style StateIn fill:#ffe1e1
    style Kernel fill:#f3e5f5
    style StateOut fill:#ffe1e1
    style Outputs fill:#e1f5ff
```

All kernel functions are pure (no side effects), with explicit inputs/outputs and deterministic behavior.

---

## Legend

- 🔵 **Blue**: User-facing (YAML, inputs/outputs)
- 🟡 **Yellow**: Core framework (loader, model, simulation)
- 🟢 **Green**: Components (graph nodes)
- 🟣 **Purple**: Kernels (pure algorithms)
- 🔴 **Red**: State (mutable state objects)
