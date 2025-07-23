# No-Code Configuration Panel

The `ConfigurationPanel.tsx` component is a crucial part of the no-code console, providing a dynamic interface for users to configure the parameters of selected nodes within their workflow. It adapts its displayed inputs based on the type of the currently selected node, ensuring a tailored and intuitive user experience.

## Key Features

*   **Dynamic Parameter Rendering:** The panel intelligently renders different input fields (text, number, select, switch, slider) based on the `nodeType` and the `getNodeConfiguration` function, which defines the expected parameters for each node type.
*   **Real-time Updates with Debounce:** Changes made to node parameters are debounced to prevent excessive updates, ensuring performance while providing a responsive feel.
*   **Node Actions:** Users can duplicate or delete the currently selected node directly from the panel.
*   **Input/Output Visualization:** It displays the input and output connections of the selected node, indicating whether inputs are connected and how many connections originate from outputs.
*   **Workflow Validation Integration:** The panel integrates with a workflow validation system, showing real-time validation status, errors, and warnings related to the node's configuration and its connections within the overall workflow.
*   **User Feedback:** Utilizes toast notifications to provide feedback on successful parameter updates.

## Component Structure and Logic

The `ConfigurationPanel` component receives `selectedNode` (the ID of the currently active node) and an optional `onNodeSelect` callback as props.

### State Management

*   `localParameters`: A local state (`useState`) that holds the parameters of the currently selected node. This is used for immediate UI updates and is debounced before being committed to the global `useNoCodeStore`.
*   `isDirty`: A boolean flag indicating if there are unsaved changes in the `localParameters`.

### Core Functions

1.  **`useEffect` for `selectedNodeData` synchronization:**
    *   When `selectedNodeData` (the selected node object from the global store) changes, `localParameters` are updated to reflect the node's current settings.
    *   This ensures the panel always displays the correct parameters for the newly selected node.

2.  **`useEffect` for external parameter changes:**
    *   Monitors changes to `selectedNodeData.data.parameters` from the global store. If changes occur externally (e.g., another part of the application modifies the node), and the local state is not dirty, `localParameters` are updated.

3.  **`debouncedUpdate` (using `useCallback` and `useRef`):**
    *   This function is responsible for applying parameter changes to the global `useNoCodeStore`.
    *   It uses a `setTimeout` to delay the update, clearing any previous timeouts if new changes occur rapidly. This prevents frequent re-renders and API calls (if applicable).
    *   After the debounce period, `updateNodeParameters` from `useNoCodeStore` is called.

4.  **`handleParameterChange`:**
    *   Updates the `localParameters` state immediately when an input field changes.
    *   Sets `isDirty` to `true`.
    *   Triggers the `debouncedUpdate` function.

5.  **`handleDeleteNode` and `handleDuplicateNode`:**
    *   Call the `removeNode` and `duplicateNode` actions from the `useNoCodeStore` respectively.

6.  **`renderParameterInput(key, config)`:**
    *   A helper function that dynamically renders the appropriate input component (`Input`, `Select`, `Switch`, `Slider`) based on the `config.type` provided for each parameter.
    *   It handles `onChange` events to update `localParameters`.

7.  **`getNodeConfiguration(nodeType)`:**
    *   This is a critical function that defines the available parameters and their configurations for each `nodeType`.
    *   It returns an object where keys are parameter names (e.g., `period`, `indicator`) and values are objects describing the input type (`type`), label, description, default value, and specific options (for `select` and `range` types).
    *   **Node Types Defined:**
        *   `technicalIndicator`: Parameters for various technical analysis indicators (SMA, RSI, Bollinger Bands, etc.), including `period`, `source`, `smoothing`, `multiplier`, `fastPeriod`, `slowPeriod`, `signalPeriod`, etc.
        *   `condition`: Parameters for logical conditions (e.g., `value`, `value2`, `lookback`, `sensitivity`, `confirmationBars`, `percentageThreshold`, `higherTimeframe`).
        *   `action`: Parameters for trading actions (e.g., `quantity`, `order_type`, `stop_loss`, `take_profit`, `trailing_distance`).
        *   `dataSource`: Parameters for data input (e.g., `assetClass`, `symbol`, `timeframe`, `startDate`, `endDate`).
        *   `customDataset`: Parameters for handling user-uploaded datasets (e.g., `fileName`, `dateColumn`, `openColumn`, `normalization`).
        *   `logic`: Parameters for logical gates (e.g., `operation`, `inputs`).
        *   `risk`: Parameters for risk management controls (e.g., `riskLevel`, `maxLoss`, `positionSize`, `drawdownLimit`).

8.  **`shouldShowField(key, config, params)`:**
    *   This helper function implements conditional rendering logic for parameters.
    *   It checks the `nodeType` and the current values of other `localParameters` to determine if a specific input field should be displayed. For example, `multiplier` is only shown for `BB` (Bollinger Bands) indicator.

9.  **`getValidationErrors()`:**
    *   Provides basic client-side validation for common parameter constraints (e.g., `period` range for indicators, `quantity` for actions).
    *   These are displayed as inline errors within the parameters tab.

10. **`getNodeInputs()` and `getNodeOutputs()`:**
    *   These functions analyze the `currentWorkflow.edges` to determine which input handles of the selected node are connected and which output handles have outgoing connections.
    *   They provide a visual representation of the node's connectivity.

## Integration with `useNoCodeStore`

The `ConfigurationPanel` heavily relies on the `useNoCodeStore` (a Zustand store) to:
*   Access the `currentWorkflow` data (nodes and edges).
*   Update node parameters (`updateNodeParameters`).
*   Remove and duplicate nodes (`removeNode`, `duplicateNode`).

## Integration with `useWorkflowValidation`

The component uses the `useWorkflowValidation` hook to get real-time validation feedback for the entire workflow. This feedback is displayed in the "Validation" tab, allowing users to identify and address issues.

## UI Components

The component leverages a set of UI components (likely from a library like Shadcn UI) for a consistent and accessible interface:
*   `Card`, `CardContent`, `CardHeader`, `CardTitle`: For structuring sections.
*   `Label`, `Input`, `Select`, `Switch`, `Slider`: For various input types.
*   `Button`: For actions like duplicate and delete.
*   `Tabs`, `TabsContent`, `TabsList`, `TabsTrigger`: For organizing configuration sections (Parameters, Inputs, Outputs, Validation).
*   `Badge`: For displaying node type and connection status.
*   `Separator`: For visual separation.
*   `useToast`: For displaying transient success messages.
*   `lucide-react` icons: For visual cues.

## How it Works (High-Level Flow)

1.  User selects a node on the no-code canvas.
2.  The `selectedNode` prop updates, triggering `useEffect` to load the node's parameters into `localParameters`.
3.  `getNodeConfiguration` is called based on the `selectedNodeData.type`, providing the schema for the node's parameters.
4.  `renderParameterInput` iterates through the schema and renders the appropriate UI controls.
5.  User modifies a parameter.
6.  `handleParameterChange` updates `localParameters` and triggers `debouncedUpdate`.
7.  After the debounce delay, `debouncedUpdate` calls `updateNodeParameters` in the `useNoCodeStore`, persisting the change to the global workflow state.
8.  The `useWorkflowValidation` hook continuously validates the workflow, and its results are displayed in the Validation tab.
