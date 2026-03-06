This repository contains everything needed to get the SWG Holocron up and running on your server. Below are the modifications, but before that is my soapbox that the developers understood there were SO MANY SYSTEMS in this game and that new players would be a bit confused starting out. A disservice being done to this game is locking knowledge behind third party sites. This was a thing in Live after NGE as well, but it did look like someone may have wanted to update it due to strings found in scripts like newbie_handoff.java. **IF YOU ARE IMPLEMENTING THIS IN A POPULATED SERVER, HIGHLY RECOMMEND WORKING NEWBIE_HANDOFF.JAVA INTO IT** That is because it triggers the opening, as well as a voice line that explains what it is. 

I have literally 0 experience for Entertainer, those are a little short. 

11 Client Files: 
**5 inside client-tools\src\game\client\library\swgClientUserInterface\src\shared\page**
#2 new: SwgCuiHolocron.h SwgCuiHolocron.cpp

_3 Modified: SwgCuiHudAction.cpp , SwgCuiHudWindowManager.cpp and .h


__
**2 inside client-tools\src\game\client\library\swgClientUserInterface\src\shared\core**

2 modified: SwgCuiMediatorFactorySetup.cpp and .h


__
**1 inside client-tools\src\engine\client\library\clientGame\src\shared\command**

1 modified: CommandCppFuncs.cpp


__
**3 inside client-tools\src\engine\client\library\clientUserInterface\src\shared\core**

3 modified: CuiKnowledgeBaseManager.cpp and h, CuiActions.h

2 Server File Modifications, skills.tab and command_table.tab

Patch included, redone input maps and the needed datatables/string files. UI had a few modifications but it was mostly bringing back old stuff. 

All input maps packaged in tre due to needing to be able to bind it. All files have a read me. If you include images in the generator, they will not be positioned correctly. It positions behind the text and to the side. Will be updated eventually




UI_Help Exists in Patch_00.tre, as it was in the game from the beginning. There were not as many entries in knowledgebase, but they were there. This was updated steadily throughout the Pre-CU. From scripts that have survived (like newbie_handoff.java) that reference it, it does seem to have had some generated missions for players and was fairly in depth of giving an example, as it looked like it guided you around a bit first as well. 
