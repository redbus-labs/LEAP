import json
import os
import time
from datetime import datetime
import inspect

import pytest

from core_agentic import agentic_base
from core_agentic import run_configs

task = None
taskCount = 0

current_test_method = ""
codeToExecute = []

def beforeExecution():
    run_configs.ref = run_configs.pageRef
    run_configs.setRef(run_configs.pageRef)
    run_configs.start_time = time.time()
    print(f"Start time: {datetime.now()}")
    agentic_base.initialSetup()
    if not run_configs.dryRun and agentic_base.page:
        print(f"🌐 Navigating to: {run_configs.url}")
        agentic_base.page.goto(run_configs.url)

def orchestrator(userTask:str = ""):
    internal_orchestrator(userTask)

def internal_orchestrator(userTask:str = ""):
    global task, taskCount
    task = userTask
    run_configs.pendingTask.append(task)
    print("-----------------ORCHESTRATOR-----------------")
    print("Current Pending Tasks: " + str(run_configs.pendingTask))
    print("Current Completed Tasks: " + str(run_configs.completedSubtasks))
    systemPrompt = (
        "You are an intelligent orchestrator responsible for selecting the next best Agent from a provided list. "
        "Each Agent has a description of its capabilities. You must choose the best Agent to start working on the pending subtask (which is part of a larger task the user wants to accomplish). "
        "Important Instruction: It’s not required that the selected Agent completes the entire pending subtask—just the most appropriate one to begin handling it.\n\n"

        "### ✅ Response Format:"
        "You must return a valid JSON object. All keys must be in double quotes. Do not include any extra keys like 'pulsed', 'effluent', etc, unless explicitly instructed. Your response must be a valid, parsable JSON string and must not include trailing commas or unquoted keys or any meta data."
        "Apart from the below mentioned JSON schema, you must not include any other text, explanation, or formatting. Your entire response must be a single valid JSON object."
        """"
        ```json
        {
            "Agent": "string, name of the selected Agent or one of the special values: TERMINATE, COMPLETE",
            "Reasoning": "string, in depth explanation for why this Agent was chosen out of all other available agents. Also specify if multiple agents were found suitable why was this preferred"
        }
        ```
        """

        "⚠️ Decision-Making Guidelines:\n"
        "0. **Task Priority Rule**: When analyzing pending subtasks, prioritize based on the order they appear in the user's original task description. Select the agent that can handle the FIRST mentioned action/requirement. Only if no agent can handle the first requirement, then consider the next requirements in sequence. Make sure to justify in the reasoning if you are skipping the first requirement with why no available agents are suitable\n"
        "1. If a subtask is not explicitly listed in the pending list, assume **it is not required—even if it's typically part of the process.**\n"
        "2. If no available Agent can fulfill the pending subtask, return `TERMINATE` as the Agent name.\n"
        "3. Avoid redoing subtasks that are already completed or available by default.\n"
        "4. If the pending task list is empty, or all subtasks are completed, return `COMPLETE`.\n"
        "5. When multiple agents are available to handle different parts of pending tasks which are explicitly mentioned, **prioritize tasks logically based on their interdependencies and decide which is the best possible agent to be chosen first**\n"
        "6. Remember, there is no such thing as immediate action requested by user. The user is requesting a task to be accomplished, and the orchestrator is responsible for selecting the best agent to start working on it. The user is not requesting an immediate action, but rather a task to be accomplished.\n"
        "7. If all required values for a logical comparison or verification (integer or string) are already captured, you must select any one agent from the available list of agents to perform the assertion. You are strictly prohibited from returning TERMINATE.\n"
        "8. If the task involves a pure browser action like refresh page or if there is an verification to be performed on page level (example: verify is X page is loaded, etc), choose any Agent from the available list of agent, even without no strong reason, never TERMINATE in this case\n\n"
        )

    userPrompt = (
        "Agents (CSV format):\n"
        f"{agentic_base.getAgentsBasedOnRef()}\n\n"
        "✅ Subtasks already completed:\n"
        f"{run_configs.completedSubtasks}\n\n"
        "🕒 Pending subtasks:\n"
        f"{run_configs.pendingTask}\n"
    )
    response = agentic_base.helper.setupLLM(provider = run_configs.llm_provider, systemPrompt=systemPrompt, userPrompt=userPrompt)
    json_response = agentic_base.helper.extract_json_block(response)
    run_configs.agent = agentic_base.helper.extractJsonValueBasedOnPath(json_response, "/Agent")
    reasoning = agentic_base.helper.extractJsonValueBasedOnPath(json_response, "/Reasoning")
    print("Agent selected by Orchestrator: " + run_configs.agent + "\nLLM Reasoning: " + reasoning)
    if run_configs.agent == "" or run_configs.agent is None or  run_configs.agent.upper().strip() == "TERMINATE":
        pytest.fail("Orchestrator could not find the next suitable agent to accomplish the pending tasks")
    elif run_configs.agent.upper().strip() == "COMPLETE":
        print("Agents have successfully completed the given task")
    else:
        functionPlanner()

def functionPlanner():
    print("-----------------FUNCTIONS PLANNER-----------------")

    systemPrompt = f"""
    You are an intelligent function planner for a UI automation agent. Your task is to generate a correct and executable sequence of function calls using **ONLY** the functions explicitly provided, always making sure the Rules defined are **strictly** followed.

    ### 📚 Provided Functions:
    You will be given three categories of functions:
    1.  **HelperFunctions** – Use via the `helper` object. These perform UI actions and require locators.
    2.  **LocatorFunctions** – Use via the `locator` object. These return locators for UI elements.
    3.  **AgentFunctions** – Use via the `agent` object. These are predefined high-level workflows.

    ---

    ### 🎯 Your Goal:
    * You must identify every minute subtasks from provided Pending tasks as a whole that are fully achievable, contextually relevant, and explicitly supported by the provided functions. If a subtask is not explicitly listed in the pending list, assume it is not required—even if it seems typical.
    * You must generate a correct and executable sequence of function calls using only the explicitly provided functions. Absolutely no new functions, assumptions, or modifications are allowed.

    ---

    ### 📏 Rules to Strictly Follow:
    1.  **TASK EXECUTION RULE:**
        1.1 Ignore the sequence of tasks until you reach an **assertion** or a **text capture** action.
            - Example: "Do A, Do B, Note down C, Do D, Do E, Verify F" →
                - If Do A is not possible, then you are allowed to perform B first if it is possible, but Note down C cannot be performed first even if Do A and B are not possible.
                - After that, D and E can again be executed in any logical order if maintaining order among D and E is not possible.
                - "Verify F" must be picked post all these.
        1.2 Always prioritize making **any achievable progress** on the **first pending subtask**.
            - Break down complex subtasks into smaller, independent actions.
            - Example: "Select X and verify Y" → Select X first, even if verifying Y is not yet possible.
            - Example: "Verify X and Y" → Verify X first, even if verifying Y is not yet possible.
            - Always execute the first achievable action, even if later actions require different function calls.
            - **Never terminate execution** if at least one action from the first subtask can still be executed.
        1.3 If there is an action to be performed before an assertion/text capture, you must perform that action first and delay the assertion/text capture (Even if it the action makes the verification impossible).
        1.4 Return TERMINATE only if no subtask at all can be completed AND no individual action from any subtask can be performed using available functions. Uncertainty about parameter handling or function behavior does not qualify for termination - attempt the function call first.
        1.5 A note to remember while deciding function calls: If an action overlays the existing screen, make sure you close the overlay once the required actions are completed, unless the next task requires the overlay to be open.

    2.  **Zero Deviation from Provided Functions:**
        - You are strictly forbidden from inventing, renaming, inferring, or altering any function. Every function used must exactly match the names and structure defined in the provided list. Any deviation from the given rules or functions is a critical violation. All rules must be followed with zero tolerance for interpretation or creativity.

    3.  **Function Reference Guidelines:**
        - Use either:
            - `AgentFunctions` directly (via `agent` object), or
            - `HelperFunctions` (via `helper`) with locators from `LocatorFunctions` (via `locator`).

    4.  **Arguments Usage Guidelines:**
        4.1 You are absolutely forbidden from using named arguments (e.g., parameter=value). All function calls must use only positional arguments.
            - **INCORRECT**: `agent.selectDate(days=7)`, `agent.selectDate(days=getConfig('<noOfDays>'))`
            - **CORRECT**: `agent.selectDate(7)`, `agent.selectDate(getConfig('<noOfDays>'))`
        4.2 All string arguments of a function must be enclosed in **double quotes**. Always assume the input data is already in the correct format. Never perform cleanup, parsing, or reformatting inside the function plan.

    5.  **Optional Functions Usage Guidelines:**
        - If the function description of a `LocatorFunctions` indicates explicitly that the presence of the field is optional, uncertain, or conditionally non-mandatory, you must wrap the entire function call within a Python `try-except` block. In the `except` block, log the message: `Note: WebElement not found. Execution continued as this is not a mandatory field.` **You are strictly prohibited to use a `try-except` block if this condition is not met.**

    6. ASSERTION/TEXT CAPTURE ISOLATION RULE - ABSOLUTE PRIORITY:
        6.1 MANDATORY ISOLATION: Any Function Plan containing `helper.assertion()`, `helper.assertionVisual()`, or `helper.getText()` MUST execute these functions as the ONLY function in the `FunctionCalls` array.
        6.2 ZERO TOLERANCE: Absolutely NO other helper function calls are permitted in the same Function Plan with isolated helper functions.
        6.3 ABSOLUTE PRECEDENCE: This rule OVERRIDES ALL other grouping, efficiency, and task completion rules without exception.
        6.4 VIOLATION CHECK: Before execution, count total functions - if >1 AND includes `helper.assertion()`/`helper.assertionVisual()`/`helper.getText()` = IMMEDIATE VIOLATION.
        6.5 CRITICAL EXEMPTION: Isolation applies ONLY to the three specified `helper.` functions. ALL other HelperFunctions, LocatorFunctions, AgentFunctions are COMPLETELY EXEMPT and MUST be grouped for efficiency.
        6.6 ENFORCEMENT VERIFICATION: Function must be the SOLE function in its FunctionCalls array to qualify as proper isolation.

        VIOLATION EXAMPLES:
        // FORBIDDEN
        [helper.assertion(), helper.click()]
        [helper.getText(), helper.assertionVisual()]

        COMPLIANT EXAMPLES:
        // CORRECT
        [helper.assertion()]
        [helper.click(), agent.selectDate()]

    7.  **FUNCTION GROUPING RULE:**
        7.1 **CRITICAL MANDATORY GROUPING**: 
        If multiple actions before an occurrence of an assertion/text capture action can be performed in a single function plan, try to group them
        Example 1: Do A, Do B and Verify C, Do D, Do E
        - Allowed: Do A and Do B in a single function plan if both are possible
        - Not allowed: Do A, Do B, Do D, Do E even if all 4 can be achieved in a single function plan as Verify C is in between  
        7.2 Only assertions/text capture require isolation - all other function types can be combined.
        7.3 When entering passenger details, fill all passenger details in a single function call, even if it requires multiple fields to be filled. Do not split passenger details into multiple function calls.
        7.4 Following Rule 7 is extremely critical even if you are following Rule 1. Remember, Rule 1 doesn't stop you from achieving subsequent subtasks along with the first subtask. So try to achieve as many subtasks as possible in a single function call while following Rule 1 and Rule 7.

    8.  🔒 **Strict Locator Preference Rules for `helper.assertionVisual()` and `helper.getText()`:**
        8.1. **Preference 1 – Exact Locator of Target Web Element**
            - Always check if the exact locator of the target element is available.
            - If available, you **must** use it.
            - ✅ Example: `helper.assertionVisual(locator.targetElement(), "Verify that target element is displayed")`
            - ❌ Do not skip this step. If unavailable, explicitly state that you checked and it does not exist.
        8.2. **Preference 2 – Exact Locator of Reference Web Element**
            - If the target locator is not available, check for a reference element locator (used in relational assertions such as above, below, near, left of, right of, etc).
            - **IMPORTANT**: The intended action of the locator (typing, clicking, etc.) does not matter — if the locator exists, you **must** use it.
            - ✅ Example: `helper.assertionVisual(locator.referenceElement(), "Verify that target element is above reference element")`
            - ❌ Never discard a valid reference locator just because it is designed for another purpose. REMEMBER: Every locator is suitable for assertion as long as the locator description makes sense.
        8.3. **Preference 3 – None as Locator**
            - Use `None` only if neither the target locator nor any reference locator exists.
            - If you use `None`, you must clearly justify that:
                * You checked for the target locator → not found.
                * You checked for reference locators → not found.
            - ✅ Example: `helper.assertionVisual(None, "Verify that target element is displayed in relation to reference element")`
            - ❌ Never jump to `None` when any locator is available.
        8.4 Assertion Granularity Rules:
            - If locators or reference locators are available under Preference 1 or Preference 2, you must assert each element individually.
            - Compound assertions are strictly prohibited in this case.
            - If locators are not available and you are using Preference 3 (i.e., passing locator=None), you are allowed to perform compound verification, provided the verification text is relevant to the Agent description.
            Example: Task: Verify A is displayed, B is displayed, C is displayed above B, D is displayed, and E is displayed.
            - Since locators exist for A and B, assert them individually (By following ASSERTION ISOLATION RULE, each assertion will be in a separate function call):
                * helper.assertVisual(locator.A, "Verify if A is displayed")
                * helper.assertVisual(locator.B, "Verify if B is displayed")
                * helper.assertVisual(locator.B, "Verify if C is displayed above B")
            - For D and E (no locators available, Preference 3 applies), compound assertion is allowed:
                * helper.assertVisual(None, "Verify if D and E are displayed")
        8.5 **CRITICAL CHECK (Enforcement)**
        - You **must** always follow this sequence: Preference 1 → Preference 2 → Preference 3.
        - Your reasoning must explicitly document:
            * Whether the target locator exists.
            * Whether the reference locator exists.
            * Why the chosen locator is the correct preference.
        - If you skip Preference 2 while a reference locator exists, it is a **RULE VIOLATION**.
        - **IMPORTANT**: If you use Preference 3, you must describe why Preference 2 cannot be used on any of the available Locators in LocatorFunctions in your Reasoning.

    9.  **LocatorFunctions Parameter Handling Rules:**
        9.1 For `LocatorFunctions` expecting string input, if no suitable string is provided in the user task, you **MUST** pass `None`. This is **MANDATORY** and the function WILL work with `None` - it is designed to handle this case. You are **STRICTLY FORBIDDEN** from assuming this makes the function unusable. `None` is a valid and expected parameter value.
        9.2 For `LocatorFunctions` which expect integer input as a parameter, if you cannot find a suitable integer provided in the user task, you **MUST** pass the default value as specified in the function description. This is **MANDATORY** and **NON-NEGOTIABLE**. You are **STRICTLY FORBIDDEN** from inventing, assuming, or inferring any integer values not explicitly present in the user task. The **ONLY** acceptable approach is:
            - If it requires forward search (first to last) → Use positive numbers (1, 2, 3...) (only if explicitly mentioned in task).
            - If it requires backward search/(last to first) → Use negative numbers (-1, -2, -3...) (only if explicitly mentioned in task).
            - 1 = first element, 2 = second element, ...
            - -1 = last element, -2 = second last element, ...
        Make sure to justify Rule 9.1 and 9.2 compliance in your reasoning.


    10. **Assertion Guidelines:**
        - For date-related assertions, you must not calculate, parse, or format dates (e.g., using `datetime`, `timedelta`, or `strftime`). The assertion should only declare the expected relation in natural form, relying on internal handling. Example: "Verify if date displayed is 7 days from today" -> **VALID** (even if current date and 7 days from today is not calculated as it will be taken care internally).
        - When performing an assertion that compares two values on UI, first capture and store each value separately (one at a time), then perform the verification using the two stored values.
        - Even if successful interaction with a certain Web Element, which is a part of user task, implicitly performs the assertion, **a separate assertion is still required**.

    11. **Data Storage Reference for Assertions:**
        11.1 For ANY assertion that references data previously captured and stored in the variables dictionary, you **MUST** retrieve and use those exact values in your assertion.
        11.2 Before writing any assertion, check the variables dictionary for relevant captured data and incorporate it using f-string formatting.
        11.3 Be it assertion or non assertion, if you want to use any value from `variables`, you should never substitute the direct value, you should always reference.
        Example: 
            If variables dictionary contains: {{"error_message": "Invalid input"}}
            Valid use (Reference from variables): f"Verify that the error message '{{variables['error_message']}}' is displayed"
            Invalid use (Direct value usage): f"Verify that the error message 'Invalid input' is displayed"
        When using any value from `variables` dictionary, make sure you justify this Rule compliance in your reasoning.

    12. **RULE FOR PLACEHOLDERS:**
        - Any placeholder enclosed in angle brackets `< >` (for example: `<source>`, `<destination>`, `<departureDays>`) must never be used directly in the code.
        - Instead, always wrap the entire placeholder with `getConfig()` (without any prefix - system adds it automatically).
        - Ensure the entire placeholder is wrapped in single quotes inside `getConfig()` and is passed as a string.
        - **Example**: `helper.type(locator.src(), getConfig('<source>'))`

    ---

    ### ✅ Response Format:
    You must return a valid JSON object. All keys must be in double quotes. Do not include any extra keys like 'pulsed', 'effluent', etc, unless explicitly instructed. Your response must be a valid, parsable JSON string and must not include trailing commas or unquoted keys or any meta data.
    Apart from the below-mentioned JSON schema, you must not include any other text, explanation, or formatting. Your entire response must be a single valid JSON object.
    ```json
    {{
      "FunctionCalls": [
        {{
          "functionCall": "string, exact Python function call using correct object prefix and only positional arguments",
          "subTask": "string, short description of the subtask accomplished by this function call. Description cannot be vague. It has to be precise. It must also mention any data values and variables used in the subtask"
        }}
      ],
      "Reasoning": "string, Explain in depth why you chose these functions from all available LocatorFunctions. Also if any assertion is being performed, explain why exactly and explain if you have strictly followed Rule 6, 7, 8, 9, 10, 11. If you did not choose any function from the provided set of functions explain why in depth",
      "PendingTasks": "string, your job is to remove the subtasks which will be achieved by all these function calls from the `Task to accomplish` and return what still needs to be done. Return the result as a single string. If all parts of the main task are already completed, return \\"None\\" (as a string, not null). Do not repeat or rephrase the completed steps. Do not modify wording unnecessarily. Only subtract exact or overlapping instructions. Ensure the final output is concise and preserves valid natural language."
    }}
    """

    userPrompt = (
        "📋 Agent Name and Description in CSV format (Agent under which LocatorFunctions are present):\n"
        f"{agentic_base.findAgentAndDescription(agentic_base.getAgentsBasedOnRef(), run_configs.agent + ',')}\n\n"

        "📦 HelperFunctions (via `helper` object):\n"
        f"{agentic_base.getTools('Helper')}\n\n"

        "🔍 LocatorFunctions (via `locator` object):\n"
        f"{agentic_base.getTools('Locator')}\n\n"

        "🤖 AgentFunctions (via `agent` object):\n"
        f"{agentic_base.getTools('Function')}\n\n"

        "🎯 Task to accomplish:\n"
        f"{task}\n\n"

        "✅ Completed subtasks:\n"
        f"{run_configs.completedSubtasks}\n\n"

        "🕒 Pending subtasks:\n"
        f"{run_configs.pendingTask}\n"

        "📋 Variables in Python Dictionary format:\n"
        f"{json.dumps(run_configs.variables)}\n\n"
    )
    response = agentic_base.helper.setupLLM(systemPrompt=systemPrompt, userPrompt=userPrompt)
    json_response = agentic_base.helper.extract_json_block(response)
    run_configs.pendingTask.clear()
    functionList = []
    count = 0
    while True:
        val = agentic_base.helper.extractJsonValueBasedOnPath(json_response, "/FunctionCalls/" + str(count) + "/functionCall")
        if val is None:
            break
        else:
            functionList.append(agentic_base.helper.extractJsonValueBasedOnPath(json_response, "/FunctionCalls/" + str(
                count) + "/functionCall"))
            run_configs.pendingTask.append(
                agentic_base.helper.extractJsonValueBasedOnPath(json_response, "/FunctionCalls/" + str(count) + "/subTask"))
            count += 1
    run_configs.pendingTask.append(agentic_base.helper.extractJsonValueBasedOnPath(json_response, "/PendingTasks"))
    print("Function Plan by Agent: " + str(functionList))
    print("Reasoning by Agent: " + agentic_base.helper.extractJsonValueBasedOnPath(json_response, "/Reasoning"))
    if not functionList:
        pytest.fail("Agent could not find any suitable functions to execute")
    else:
        if functionList[0] == "TERMINATE":
            pytest.fail("Agent could not find any suitable functions to execute")
        else:
            functionExecutor(functionList)

def functionExecutor(functionList):
    global task
    print("-----------------FUNCTIONS EXECUTOR-----------------")
    exception = ""

    for value in functionList:
        value = value.replace("getConfig(", "agentic_base.getConfig(")
        
        # Replace object references with full paths
        value = value.replace("variables[", "run_configs.variables[")
        value = value.replace("helper.", "agentic_base.helper.")
        value = value.replace("locator.", "agentic_base.POR." + run_configs.ref + "()." + run_configs.agent + "().")
        value = value.replace("agent.", "agentic_base.POR." + run_configs.ref + "()." + run_configs.agent + "().")
        try:
            print(value)
            exec(value)
            run_configs.codeStorage.append(value)
            run_configs.completedSubtasks.append(run_configs.pendingTask.pop(0))
        except Exception as e:
            print("Exception occurred while executing the above function: " + str(e))
            exception = str(e)
            run_configs.failedSubTask = run_configs.pendingTask.pop(0)
            break 
    agentic_base.refChangeCheck()
    if exception == "":
        learnerAgent()
    else:
        print("Failed: " + str(run_configs.failedSubTask))
        failureAnalyzer(exception)

def learnerAgent():
    global task
    if run_configs.countOfConsecutiveFailures > 0:
        print("-----------------LEARNER------------------")
        print("Learning: " + str(run_configs.learnerList))
        systemPrompt = (
            "You are a validation assistant for checking whether a new learning already exists in a given Learning Document.\n\n"

            "The Learning Document contains records with the following fields:\n"
            "- Failed Subtask\n"
            "- Failure Reason\n"
            "- Agent Selected\n"
            "- Reasoning for Agent Selection\n"
            "- Task to Perform (To Mitigate Failure)\n\n"

            "📄 Document Contents:\n"
            f"{agentic_base.readLearner()}\n\n"

            "🧠 Your Task:\n"
            "Compare the new learning (provided in the user prompt) against the records in the Learning Document. "
            "A match is considered valid **only if** all the following 5 fields are semantically similar:\n"
            "- Failed Subtask\n"
            "- Failure Reason\n"
            "- Agent Selected\n"
            "- Reasoning for Agent Selection\n"
            "- Task to Perform (To Mitigate Failure)\n\n"

            "🟢 If such a matching record exists, return:\n"
            "- `output`: \"true\"\n"
            "- `ID`: the exact ID of the matching record\n"

            "🔴 If no such record exists, OR if the first three fields match but the **Reasoning for Agent Selection or Mitigation Task is different**, return:\n"
            "- `output`: \"false\"\n"
            "- `ID`: \"NA\"\n\n"

            "✅ Response Format (strict JSON):\n"
            "{\n"
            "  \"output\": \"true or false\",\n"
            "  \"ID\": \"string — ID of the matching record, or 'NA' if not found\",\n"
            "  \"reasoning\": \"Short explanation for why true or false was chosen\"\n"
            "}"
        )
        userPrompt = str(run_configs.learnerList)
        run_configs.countOfConsecutiveFailures = 0
        response = agentic_base.helper.setupLLM(systemPrompt=systemPrompt, userPrompt=userPrompt)
        json_response = agentic_base.helper.extract_json_block(response)
        output = agentic_base.helper.extractJsonValueBasedOnPath(json_response, "/output")
        reasoning = agentic_base.helper.extractJsonValueBasedOnPath(json_response, "/reasoning")
        idVal = agentic_base.helper.extractJsonValueBasedOnPath(json_response, "/ID")
        print("Output: " + output + " ID: " + idVal + "\nReasoning: " + reasoning)
        if output.lower().strip() == "false":
            print("No suitable record found in Learning Document. Adding new record")
            learner_path = os.path.join(run_configs.get_project_root(), "learner.csv")
            agentic_base.append_record_to_csv(learner_path, run_configs.learnerList)
    internal_orchestrator()

def failureAnalyzer(exception: str):
    print("-----------------FAILURE ANALYZER-----------------")
    if "assertion" in exception.lower():
        print("Skipping Failure Analysis")
        pytest.fail(exception)
        return
    run_configs.countOfConsecutiveFailures = run_configs.countOfConsecutiveFailures+1
    print ("Consecutive Failures Count: " + str(run_configs.countOfConsecutiveFailures))
    if run_configs.countOfConsecutiveFailures>=2:
        pytest.fail("Consecutive failures exceeded limit. Terminating execution.")
        agentic_base.afterExecutionCleanup()
        return
    else:
        whatsOnUI = agentic_base.helper.askLLMAboutImage(agentic_base.helper.take_screenshot_as_base64())
        systemPrompt = (
            "You are a failure recovery assistant responsible for selecting the best agent to mitigate a failed subtask in a UI automation task.\n\n"

            "🎯 Objective:\n"
            "Identify which agent can recover from the failure and what exact task that agent should perform to overcome the issue and allow continuation of the overall user task.\n\n"

            "📦 Expected Output (strict JSON):\n"
            "{\n"
            "  \"Agent\": \"string — Name of the selected agent, or 'TERMINATE' if no agent is suitable\",\n"
            "  \"Reasoning\": \"string — Why this agent is appropriate to recover from the failure\",\n"
            "  \"task\": \"string — Specific recovery task the agent should perform to mitigate the failure. Do not include unrelated or extra steps.\",\n"
            "  \"failureReason\": \"string — Likely reason the subtask failed, based on UI description and error message\",\n"
            "  \"decisionFactor\": \"string — Return 'LEARNER AGENT' if this decision is based on past learnings; otherwise, return 'FRESH ANALYSIS'\"\n"
            "}\n\n"

            "🧠 Decision-Making Instructions:\n"
            "1. First, check for any matching records in the past Learnings. If you find a matching recovery strategy, prefer that.\n"
            "2. If no suitable learning is found or you're uncertain, proceed with fresh analysis.\n"
            "3. Consider only the explicitly listed subtasks — ignore implicit steps.\n"
            "4. If the failed subtask is not required based on the user’s task, and no agent is needed to handle it, you may choose to ignore it (e.g., dismissing a popup).\n"
            "5. Do not attempt actions for items that are available by default.\n"
            "6. If no agent is suitable, return:\n"
            "{ \"Agent\": \"TERMINATE\", \"Reasoning\": \"No agent suitable for any remaining subtask.\", ... }\n"
        )
        userPrompt = (
            "📋 Agents List and Descriptions (CSV):\n"
            f"{agentic_base.getAgentsBasedOnRef()}\n\n"

            "🎯 User's Overall Task:\n"
            f"{task}\n\n"

            "✅ Completed Subtasks:\n"
            f"{run_configs.completedSubtasks}\n\n"

            "🕗 Pending Subtasks:\n"
            f"{run_configs.pendingTask}\n\n"

            "❌ Failed Subtask:\n"
            f"{run_configs.failedSubTask}\n\n"

            "🧩 Current UI State:\n"
            f"{whatsOnUI}\n\n"

            "🐞 Playwright Error Message:\n"
            f"{str(exception)}\n\n"

            "📚 Past Learnings:\n"
            f"{agentic_base.readLearner()}"
        )
        response = agentic_base.helper.setupLLM(systemPrompt=systemPrompt, userPrompt=userPrompt)
        json_response = agentic_base.helper.extract_json_block(response)
        run_configs.agent = agentic_base.helper.extractJsonValueBasedOnPath(json_response, "/Agent")
        reasoning = agentic_base.helper.extractJsonValueBasedOnPath(json_response, "/Reasoning")
        failureMitigationTask = agentic_base.helper.extractJsonValueBasedOnPath(json_response, "/task")
        failureReason = agentic_base.helper.extractJsonValueBasedOnPath(json_response, "/failureReason")
        decisionFactor = agentic_base.helper.extractJsonValueBasedOnPath(json_response, "/decisionFactor")
        print("Agent Selected by Failure Analyzer Agent: " + run_configs.agent + "\nLLM Reasoning: " + reasoning + "\nTask to be performed: " + failureMitigationTask + "\nFailure Reason: " + failureReason + "\nDecision Factor: " + decisionFactor)
        run_configs.learnerList = {"Failed Subtask": run_configs.failedSubTask, "Failure Reason": failureReason, "Agent Selected": run_configs.agent, "Reasoning for Agent Selection": reasoning, "Task to Perform": failureMitigationTask}
        run_configs.pendingTask.insert(0, failureMitigationTask)
        run_configs.pendingTask.insert(1, run_configs.failedSubTask)
        run_configs.failedSubTask = ""
        if run_configs.agent.upper().strip() == "TERMINATE":
            pytest.fail("Failure Analyzer could not find a suitable agent available to mitigate failure. Terminating execution")
            agentic_base.afterExecutionCleanup()
        functionPlanner()