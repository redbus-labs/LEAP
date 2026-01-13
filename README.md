
# L.E.A.P (LLM-driven Execution & Automation Platform)

This framework leverages Agentic AI to autonomously execute frontend test cases written in natural English and dynamically generate test automation code based on a library of pre-defined tools and agents.

---

## Table of Contents
- [Mandatory Pre Read](#mandatory-pre-read)
- [Project Structure](#project-structure)
- [Config Usage in Test Cases](#config-usage-in-test-cases)
- [Onboarding Checklist for a New Agent](#onboarding-checklist-for-a-new-agent)
- [Tool Onboarding Process](#tool-onboarding-process)
- [Locator Best Practices](#locator-best-practices)
- [Additional Requirements](#additional-requirements)
- [Quick Start](#quick-start)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Acknowledgements](#acknowledgements)
- [Issues and Support](#issues-and-support)

---
## MANDATORY PRE-READ

[Link](https://medium.com/@krishna.d.hegde/l-e-a-p-6b73e748de33)

---
## Project Structure

```
leap-agentic/
├── src/
│   ├── core_agentic/
│   │   ├── agentic.py                     # Core AI modules and LLM logic
│   │   ├── agentic_base.py                # Hooks, setup/teardown, and workflow support
│   │   ├── test_trial.py                  # Playground for English-based test execution
│   │   ├── run_configs.py                 # Configs to control execution (e.g., channel, LLM model)
│   └── main/
│       ├── agent_group/                   # Folder for each agent group (e.g., redBus Home Page)
│       │   ├── agent/                     # Folder for each agent (e.g., Search Form)
│       │   │   ├── agent_details.py       # Agent metadata (Name, Description)
│       │   │   └── tools/                 # Tools available for the agent
│       │   │       ├── definitions/       # Abstract tool signatures for AI
│       │   │       │   ├── agent_locator_tools.py   # Web element abstracts
│       │   │       │   └── agent_function_tools.py  # Business flow abstracts
│       │   │       └── implementation/    # Platform-specific implementations
│       │   │           ├── android.py
│       │   │           ├── ios.py
│       │   │           ├── mweb.py
│       │   │           └── dweb.py
│       ├── por/                           # Page Object Repository (Singleton pattern)
│       │   ├── por_agent_group.py         # File for agent group comprising agent objects
│       │   └── por_master.py              # Master repository with all agent group PORs
│       └── utilities/
│           └── helper/                    # Frontend Automation "Super Helper"
│               ├── helper_definition.py           # Abstract methods/capabilities shared with AI
│               ├── helper_common_implementation.py # Cross-platform logic & internal framework tools
│               ├── helper_apps_implementation.py   # App-specific logic (Gestures, Contexts)
│               └── helper_browser_implementation.py # Web-specific logic (Cookies, Window handles)
│   └── resources/
│       └── configs/
│           ├── common.yaml               # Cross-platform common configs
│           ├── mweb.yaml                 # MWeb-specific config
│           ├── dweb.yaml                 # DWeb-specific config
│           ├── android.yaml              # Android-specific config
│           └── ios.yaml                  # iOS-specific config
├── credentials.json                      # Your API keys (not tracked in git)
├── credentials.json.example              # Template for credentials (safe to commit)
├── agent_onboarding.md                   # Context for AI-based agent onboarding
├── learner.csv                           # File where learnings are recorded
```

---

## Config Usage in Test Cases

When writing test cases in natural language, configuration values can be referenced using angular brackets (`< >`).

**Example:**

Without config:

```
Search for ferries from Location-1 Chhangg to Location-2
```

With config:

```
Search for ferries from <source> to <destination>
```

Here, `<source>` and `<destination>` are automatically picked from the corresponding configuration file.

---

## Onboarding Checklist for a New Agent

1. Create an agent group folder:

   ```
   src/main/agent_group/<group_name>/
   ```

2. Create a POR for the group:

   ```
   src/main/por/por_<group_name>.py
   ```

   Register it in `por_master.py`.

3. Set up the agent structure:

   ```
   agent_group/<group_name>/
   ├── agent_details.py
   └── tools/
       ├── definitions/
       │   ├── agent_locator_tools.py
       │   └── agent_function_tools.py
       └── implementation/
           ├── android.py
           ├── ios.py
           ├── mweb.py
           └── dweb.py
   ```

### OR

Use an AI-powered IDE (or any IDE with GitHub Copilot enabled):

* Add `agent_onboarding.md` as context
* Tell the AI you want to onboard a new agent
* Answer the questions prompted by the AI
* Sit back and let the AI handle the onboarding process 🙂

---

## Tool Onboarding Process

When onboarding a new tool, declare all tool definitions as abstract methods in the appropriate base class:

* `agent_locator_tools` → Locator-related tools
* `agent_function_tools` → Action or function-based tools

### 1. Static Tool Definition

Use this pattern for elements or actions that do not require parameters.

```python
@abstractmethod
def search_button(self):
    """
    Search button to search all ferries available.
    """
    pass
```

**Guidelines:**

* Method name should clearly represent the UI element or action
* Add a concise docstring explaining the purpose
* No parameters are required

### 2. Dynamic Tool Definition (With Parameters)

Use this pattern when the tool requires runtime inputs.

```python
@abstractmethod
def ferryTupleByFerryName(
    self,
    ferryName: Annotated[str, "Name of the ferry"],
    ferryOccurence: Annotated[int, "Position among multiple ferries (Default: 1)"]
):
    """
    Returns the ferry tuple based on ferry name or ferry operator name.
    """
    pass
```

**Guidelines:**

* Use `Annotated[type, "description"]` for parameters
* Clearly describe each parameter
* Mention default values explicitly in descriptions
* Add a meaningful docstring

---

## Locator Best Practices

1. **Maximize Coverage with Minimal Locators**

* Prefer flexible, descriptive selectors
* Reduce locator count and maintenance effort

2. **Tag Reference-Changing Locators to the Appropriate Agent Group**
If a locator interaction changes the page or context, tag it with the correct agent group reference.

```python
run_configs.setRef("search_result_page")
```

3. **Use Dynamic Parameters**

* Substitute dynamic values as placeholders in locator strings
* Pass actual values at runtime

4. **Enable Self-Healing**

* Always wrap locators with `selfHeal()`
* Enables recovery from minor UI changes (WIP)

### Example

```python
def ferryTupleByBusName(
    self,
    ferryName: Annotated[str, "Name of the ferry operator"],
    ferryOccurence: Annotated[int, "Position among multiple ferries (Default: 1)"]
):
    run_configs.setRef("time_selection_page")
    return agentic_base.helper.selfHeal(
        "(//*[@data-autoid='inventoryList']"
        "//*[contains(@class,'travelsName_') and text()='{ferryName}']"
        "//ancestor::*[contains(@class,'tupleWrapper_')])[{ferryOccurence}]",
        ferryName,
        ferryOccurence
    )
```

---

## Additional Requirements

### 1. Define Section Locators in Tool Implementation Constructors

Each agent represents a specific section or component of a page. Root locator(s) must be defined in the constructor.

**Single Section Locator:**

```python
class search_widget:
    def __init__(self):
        run_configs.section_locator = ["//div[@data-section='abcd']"]
```

**Multiple Section Locators:**

```python
class search_widget:
    def __init__(self):
        run_configs.section_locator = [
            "//div[@id='abcd']",
            "//div[@data-component='xyz']"
        ]
```

### 2. Explain Agent Groups in `refChangeCheck()`

**Location:** `core_agentic/agentic_base -> refChangeCheck()`

Each `agent_group` must have a brief textual explanation describing what it represents on the UI.

**Purpose:**

* Accurate page/section change validation
* Helps the AI understand context transitions
* Ensures correct agents are supplied after navigation

---

## Quick Start

### Prerequisites

* Python 3.13 or later
* LLM API key (Gemini recommended - [Guide](https://chatgpt.com/share/695b7e82-d950-8001-bbf0-a3a949e375d1))

### Try It Out

1. **Clone the repository**
   ```bash
   git clone https://github.com/redbus-labs/LEAP
   cd LEAP
   ```
2. [Install dependencies](https://chatgpt.com/share/695f5b4c-b5e0-8001-843e-e98e968a8e5a) (from `requirements.txt`)
3. **Set up credentials** (choose one method):

   **Method 1: Environment Variables (Recommended)**
   ```bash
   export GEMINI_API_KEY='your-api-key-here'
   ```
   
   **Method 2: JSON File (Alternative)**
   ```bash
   cp credentials.json.example credentials.json
   # Edit credentials.json and add your API keys
   ```
   
   > **Security Note**: 
   > - The `credentials.json` file is already in `.gitignore` and will not be committed to the repository
   > - `credentials.json.example` is a template file (safe to commit) that shows the expected structure
   > - **Environment variables are strongly recommended** as they prevent accidental credential exposure in code, logs, or version control
   > - Never commit actual credentials to the repository
4. Execute the sample test case under `core_agentic/test_trial.py`


### Few Points to Keep in Mind

* The quality of descriptions directly impacts accuracy
* Recommended LLMs [As of 14 Jan 2026] : Gemini 2.5 Pro/Gemini 3 Pro
* Keep the LLM's `thinking` enabled in run configurations for better results.

---

## Roadmap

* Android and iOS onboarding
* Reporting
* Token optimization
* Mocking support
* Modularizing generated code
* Autonomous code storage in DB

---

## Contributing

We welcome contributions from the community! This project can only evolve with open source contributions.

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please read our [Contributing Guidelines](https://github.com/redbus-labs/LEAP/blob/main/CONTRIBUTING.md) before submitting contributions.

### Development Setup

1. Clone the repository
2. Import into your IDE
3. Run tests to ensure everything works
4. Start coding!


---

## Acknowledgements

**Architected and Developed by**:
[Krishna Hegde](https://www.linkedin.com/in/krishna-d-hegde/), Senior SDET, redBus

**Guided and Mentored by**:
[Chandrashekar Patil](https://www.linkedin.com/in/patilchandrashekhar/), Senior Director – QA, redBus

**Special Thanks**:

* [Smruti Sourav Sahoo](https://www.linkedin.com/in/smruti-sourav-2000/), SDET, redBus — for supporting the development efforts and being an early adopter of the project
* [Vishnuvardhan Reddy Bhumannagari](https://www.facebook.com/share/1GHW8SHjLq), Senior SDET Manager, redBus — for introducing visual assertions at redBus
* [Rithish Saralaya](https://www.linkedin.com/in/rithish/), SVP Engineering, redBus — for organizing Project Nirman, an AI-first initiative that helped uncover key gaps in the framework and fast-track its growth.

---
## Issues and Support

Found a bug or need help? Please [open an issue](https://github.com/redbus-labs/LEAP/issues) on GitHub.

---
