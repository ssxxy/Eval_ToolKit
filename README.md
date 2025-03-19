# Eval_ToolKit
 Eval Toolkit code dummy by SY


This code is Indivial Code dummy from EVAL TEAM Project. 
You may find whole codes in here. https://github.com/eval-nva5th/maya_usd.git

This is KEY Functions :

1. UserInfo | TaskInfo | ClickedTask in loader
    - UserInfo: Retrieves and verifies the user's information.
    - TaskInfo: Fetches data from Shotgrid and stores it in a nested dictionary format.
    - ClickedTask: When a task is clicked in the task table, one of the nested dictionaries retrieved by TaskInfo is used as a parameter to create the object variable and associates with object class. This object will be used later for Side Widget interactions and for publishing process.

2. Side Widget
: A custom widget, which is in the Maya workspace provides an overview of task-related information. The widget is generated on the right side when a file is opened in the loader, and it can be closed and reopened. 
It contains..
    - Information about one task and its related entity, with real-time task status update functionality.
    - Information about other artists working on the same entity.
    - Information of the latest notes attached to the latest published file.

3. System Path
: Sets the root path based on the operating system (Mac OS and Linux).
This class allows the root path to be easily set for all files, enabling the code to function seamlessly across both operating systems with a single implementation.