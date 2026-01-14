# Agent Onboarding Guide

## Step 1: Collect Required Details
Ask user for:
- **Page name** (must end with _page)
- **Agent name**
- **Agent description**

---

## Step 2: Create Agent Folder Structure
**Path:**

    src/main/agent_groups/{page}/agents/{agent_name}/

- If the agent already exists → notify user (skip creation).

---

## Step 3: Generate `agent_details.py`
**Template:**

```python
class common:
    agent_name = "<agent_name>"
    agent_description = "<agent_description>"

class mweb(common):
    pass

class dweb(common):
    pass

class android(common):
    pass

class ios(common):
    pass
```

---

## Step 4: Create Tools Folder Structure
```
tools/
   ├── definition/
   │     ├── agent_function_tools.py
   │     └── agent_locator_tools.py
   └── implementation/
         └── web.py
         └── android.py
         └── ios.py
         
```

---

## Step 5: Populate Definition Files
**agent_function_tools.py**
```python
from abc import abstractmethod
from typing import Annotated

class common:
    pass

class mweb(common):
    pass

class dweb(common):
    pass

class android(common):
    pass

class ios(common):
    pass
```

**agent_locator_tools.py**
```python
from abc import abstractmethod
from typing import Annotated

class common:
    def __init__(self):
        pass

class mweb(common):
    pass

class dweb(common):
    pass

class android(common):
    pass

class ios(common):
    pass
```

---

## Step 6: Populate Implementation File
**web.py**
```python
from typing import Annotated
import core_agentic.agentic_base as agentic_base
from core_agentic import run_configs
from ..definition.agent_locator_tools import mweb as LocatorToolsMweb
from ..definition.agent_locator_tools import dweb as LocatorToolsDweb
from ..definition.agent_function_tools import mweb as FunctionToolsMweb
from ..definition.agent_function_tools import dweb as FunctionToolsDweb

class <agent name>(LocatorToolsMweb, LocatorToolsDweb, FunctionToolsDweb, FunctionToolsMweb):
    def __init__(self):
        run_configs.SECTION_AUTO_ID = []
```

**android.py**
```python
from typing import Annotated
import core_agentic.agentic_base as agentic_base
from core_agentic import run_configs
from ..definition.agent_locator_tools import android as LocatorTools
from ..definition.agent_function_tools import android as FunctionTools

class <agent name>(LocatorTools, FunctionTools):
    def __init__(self):
        run_configs.SECTION_AUTO_ID = []
 
```

**ios.py**
```python
from typing import Annotated
import core_agentic.agentic_base as agentic_base
from core_agentic import run_configs
from ..definition.agent_locator_tools import ios as LocatorTools
from ..definition.agent_function_tools import ios as FunctionTools

class <agent name>(LocatorTools, FunctionTools):
    def __init__(self):
        run_configs.SECTION_AUTO_ID = []
 
```

---

## Step 7: Create / Update POR files
**In:**

    src/main//por/por_<page name>.py

```python
class <PageName>_POR():
    obj_<agent_name> = None

    def <agent_name>(self):
        if <PageName>_POR.obj_<agent_name> is None:
            if run_configs.channel.lower().strip() == "dweb" or run_configs.channel.lower().strip() == "mweb":
                from ..agent_groups.<PageName>.agents.<agent_name>.tools.implementation.web import <agent name>
                <PageName>_POR.obj_<agent_name> = <agent_name>()
            elif run_configs.channel.lower().strip() == "android":
                from ..agent_groups.<PageName>.agents.<agent_name>.tools.implementation.android import <agent_name>
                <PageName>_POR.obj_<agent_name> = <agent_name>()
            elif run_configs.channel.lower().strip() == "ios":
                from ..agent_groups.<PageName>.agents.<agent_name>.tools.implementation.ios import <agent_name>
                <PageName>_POR.obj_<agent_name> = <agent_name>()
        return <PageName>_POR.obj_<agent_name>
```

**In por_agents.py → update Agents_POR class with:**

```python
obj_<page name>: <PageName>_POR = None

def <page name>(self):
    if Agents_POR.obj_<page name> is None:
        Agents_POR.obj_<page name> = <PageName>_POR()
    return Agents_POR.obj_<page name>
```

---

## ✅ Once all steps are done → Agent onboarding is complete.

