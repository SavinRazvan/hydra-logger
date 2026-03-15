# Hydra-Logger Workflow Architecture

This document describes runtime workflows and interaction boundaries.

For module-level ownership and symbol detail, use `docs/modules/README.md`.

## Workflow Scope

- Logging call path (sync, async, composite variants)
- Layer routing and destination dispatch
- Formatter selection behavior
- Extension processing points
- Factory-to-runtime instantiation path

## End-To-End Logging Pipeline

```mermaid
flowchart TD
  userCall[UserLogCall] --> loggerEntry[LoggerEntryPoint]
  loggerEntry --> createRecord[CreateLogRecord]
  createRecord --> extensionStep{ExtensionsEnabled}
  extensionStep -->|No| routeLayer[ResolveLayer]
  extensionStep -->|Yes| extensionProcess[ProcessThroughExtensions]
  extensionProcess --> routeLayer
  routeLayer --> levelCheck[LevelThresholdCheck]
  levelCheck -->|BelowThreshold| stopDrop[DropMessage]
  levelCheck -->|Pass| resolveHandlers[ResolveHandlersForLayer]
  resolveHandlers --> formatterSelect[SelectFormatter]
  formatterSelect --> handlerEmit[EmitToDestination]
  handlerEmit --> doneNode[Done]
```

## Logger Variant Workflows

### SyncLogger

```mermaid
sequenceDiagram
  participant User as UserCode
  participant SyncLog as SyncLogger
  participant Handler as Handler
  participant Dest as Destination

  User->>SyncLog: info/warning/error(...)
  SyncLog->>SyncLog: create_log_record(...)
  SyncLog->>SyncLog: resolve layer and level
  SyncLog->>Handler: handle(record)
  Handler->>Dest: emit(formatted record)
  Dest-->>Handler: result
  Handler-->>SyncLog: return
  SyncLog-->>User: return
```

### AsyncLogger

```mermaid
sequenceDiagram
  participant User as UserCode
  participant AsyncLog as AsyncLogger
  participant Handler as AsyncCapableHandler
  participant Dest as Destination

  User->>AsyncLog: log/log_async(...)
  AsyncLog->>AsyncLog: create_log_record(...)
  AsyncLog->>AsyncLog: async or sync fallback path
  AsyncLog->>Handler: emit_async(record) or emit(record)
  Handler->>Dest: write payload
  Dest-->>Handler: result
  Handler-->>AsyncLog: return
  AsyncLog-->>User: task/coroutine resolved
```

### Composite Logger Family

```mermaid
flowchart LR
  compositeEntry[CompositeLoggerCall] --> fanOut[FanOutToComponents]
  fanOut --> componentA[ComponentLoggerA]
  fanOut --> componentB[ComponentLoggerB]
  fanOut --> componentN[ComponentLoggerN]
  componentA --> aggregateResult[AggregateHealthAndStatus]
  componentB --> aggregateResult
  componentN --> aggregateResult
```

## Layer Routing Workflow

```mermaid
flowchart TD
  requestLayer[RequestedLayer] --> layerExists{LayerExists}
  layerExists -->|Yes| useRequested[UseRequestedLayerHandlers]
  layerExists -->|No| hasDefault{DefaultLayerExists}
  hasDefault -->|Yes| useDefault[UseDefaultLayerHandlers]
  hasDefault -->|No| anyLayer{AnyLayerAvailable}
  anyLayer -->|Yes| useAny[UseAnyAvailableLayer]
  anyLayer -->|No| noHandlers[NoHandlersResolved]
```

## Formatter Selection Workflow

```mermaid
flowchart LR
  destinationConfig[DestinationConfig] --> formatType[format field]
  formatType --> formatterLookup[get_formatter]
  formatterLookup --> knownFormat{KnownFormat}
  knownFormat -->|Yes| formatterInstance[FormatterInstance]
  knownFormat -->|No| defaultPlain[PlainTextFallback]
  formatterInstance --> formattedPayload[FormattedPayload]
  defaultPlain --> formattedPayload
```

## Factory Workflow

```mermaid
flowchart TD
  factoryCall[FactoryCall] --> chooseType[SelectLoggerType]
  chooseType --> normalizeCfg[NormalizeOrBuildConfig]
  normalizeCfg --> instantiateLogger[InstantiateLogger]
  instantiateLogger --> setupLayers[SetupLayersAndHandlers]
  setupLayers --> returnLogger[ReturnConfiguredLogger]
```

## Cross-Module Interaction Map

```mermaid
graph TD
  loggersPkg[loggers] --> handlersPkg[handlers]
  loggersPkg --> formattersPkg[formatters]
  loggersPkg --> configPkg[config]
  loggersPkg --> typesPkg[types]
  loggersPkg --> extensionsPkg[extensions]
  loggersPkg --> utilsPkg[utils]
  factoriesPkg[factories] --> loggersPkg
  factoriesPkg --> configPkg
  handlersPkg --> formattersPkg
  handlersPkg --> typesPkg
```

## Maintenance Rules

- Treat `docs/modules/*.md` as canonical for module behavior and export details.
- Update this workflow document only when execution flow changes.
- Keep diagrams synchronized with current logger, handler, formatter, and factory behavior.
