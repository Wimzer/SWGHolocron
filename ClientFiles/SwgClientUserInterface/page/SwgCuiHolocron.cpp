//======================================================================
//
// SwgCuiHolocron.cpp
// Copyright Sony Online Entertainment
//
//======================================================================

#include "swgClientUserInterface/FirstSwgClientUserInterface.h"
#include "swgClientUserInterface/SwgCuiHolocron.h"

#include "clientGame/ClientCommandQueue.h"
#include "clientUserInterface/CuiActionManager.h"
#include "clientUserInterface/CuiActions.h"
#include "clientUserInterface/CuiKnowledgeBaseManager.h"
#include "clientUserInterface/CuiManager.h"
#include "UIButton.h"
#include "UIButtonStyle.h"
#include "UIDataSourceContainer.h"
#include "UIImage.h"
#include "UIPage.h"
#include "UIText.h"
#include "UITreeView.h"

//======================================================================

namespace SwgCuiHolocronNamespace
{
	static const UILowerString KBNodeNameProperty = UILowerString("KBNodeNameProperty");
	static const UILowerString KBLinkTargetProperty = UILowerString("KBLinkTargetProperty");
	static const UILowerString KBCommandProperty = UILowerString("KBCommandProperty");

	std::string const cms_linkButton("linkButton");

	Unicode::String const cms_expandAllStyle(Unicode::narrowToWide("/Styles.tree.image.expanded"));
	Unicode::String const cms_collapseAllStyle(Unicode::narrowToWide("/Styles.tree.image.collapsed"));
}

using namespace SwgCuiHolocronNamespace;

//======================================================================

SwgCuiHolocron::SwgCuiHolocron(UIPage & page) :
CuiMediator                ("SwgCuiHolocron", page)
, UIEventCallback          ()
, m_treeTopics             (0)
, m_entryText              (0)
, m_entryTitle             (0)
, m_textInfo               (0)
, m_entryComp              (0)
, m_imageSample            (0)
, m_buttonBack             (0)
, m_buttonNext             (0)
, m_buttonClose            (0)
, m_buttonExit             (0)
, m_buttonServices         (0)
, m_buttonBug              (0)
, m_buttonReportPlayer     (0)
, m_buttonReload           (0)
, m_buttonSample           (0)
, m_textSample             (0)
, m_navigationHistory      ()
, m_navigationIndex        (-1)
, m_currentPageName        ()
, m_syncingTree            (false)
{
	getCodeDataObject(TUITreeView,  m_treeTopics,        "treeTopics");
	getCodeDataObject(TUIText,      m_entryText,         "entrytext");
	getCodeDataObject(TUIText,      m_entryTitle,        "entrytitle");
	getCodeDataObject(TUIText,      m_textInfo,          "textInfor");
	getCodeDataObject(TUIPage,      m_entryComp,         "entrycomp");
	getCodeDataObject(TUIImage,     m_imageSample,       "imagesample");
	getCodeDataObject(TUIButton,    m_buttonBack,        "buttonback");
	getCodeDataObject(TUIButton,    m_buttonNext,        "buttonnext");
	getCodeDataObject(TUIButton,    m_buttonClose,       "buttonclose");
	getCodeDataObject(TUIButton,    m_buttonExit,        "buttonExit");
	getCodeDataObject(TUIButton,    m_buttonServices,    "buttonservices");
	getCodeDataObject(TUIButton,    m_buttonBug,         "buttonbug");
	getCodeDataObject(TUIButton,    m_buttonReportPlayer,"buttonReportPlayer");
	getCodeDataObject(TUIButton,    m_buttonSample,      "buttonSample");
	getCodeDataObject(TUIText,      m_textSample,        "textSample");

	// Optional debug reload button
	UIButton * debugButton = 0;
	getCodeDataObject(TUIButton, debugButton, "buttonreload", true);
	if (debugButton)
	{
		m_buttonReload = debugButton;
		registerMediatorObject(*m_buttonReload, true);
	}

	registerMediatorObject(*m_treeTopics,        true);
	registerMediatorObject(*m_buttonBack,        true);
	registerMediatorObject(*m_buttonNext,        true);
	registerMediatorObject(*m_buttonClose,       true);
	registerMediatorObject(*m_buttonExit,        true);
	registerMediatorObject(*m_buttonServices,    true);
	registerMediatorObject(*m_buttonBug,         true);
	registerMediatorObject(*m_buttonReportPlayer,true);

	m_entryTitle->SetPreLocalized(true);
	m_entryTitle->Clear();
	m_entryText->SetPreLocalized(true);
	m_entryText->Clear();
	m_textInfo->SetPreLocalized(true);

	m_buttonSample->SetVisible(false);
	m_textSample->SetVisible(false);
	m_imageSample->SetVisible(false);

	m_buttonBack->SetEnabled(false);
	m_buttonNext->SetEnabled(false);

	setState(MS_closeable);
	setState(MS_closeDeactivates);
}

//----------------------------------------------------------------------

SwgCuiHolocron::~SwgCuiHolocron()
{
	m_treeTopics         = 0;
	m_entryText          = 0;
	m_entryTitle         = 0;
	m_textInfo           = 0;
	m_entryComp          = 0;
	m_imageSample        = 0;
	m_buttonBack         = 0;
	m_buttonNext         = 0;
	m_buttonClose        = 0;
	m_buttonExit         = 0;
	m_buttonServices     = 0;
	m_buttonBug          = 0;
	m_buttonReportPlayer = 0;
	m_buttonReload       = 0;
	m_buttonSample       = 0;
	m_textSample         = 0;
}

//----------------------------------------------------------------------

void SwgCuiHolocron::performActivate()
{
	CuiManager::requestPointer(true);

	// Re-warm body strings in case they were GC'd since the loading screen.
	// When called after a fresh zone-in this is near-instant (cache hits only).
	CuiKnowledgeBaseManager::warmAllBodyStrings();

	populateTopicTree();

	if (m_currentPageName.empty())
	{
		loadPage("Root");
	}
}

//----------------------------------------------------------------------

void SwgCuiHolocron::performDeactivate()
{
	CuiManager::requestPointer(false);
}

//----------------------------------------------------------------------

void SwgCuiHolocron::OnButtonPressed(UIWidget * context)
{
	if (context == m_buttonClose || context == m_buttonExit)
	{
		closeThroughWorkspace();
	}
	else if (context == m_buttonBack)
	{
		navigateBack();
	}
	else if (context == m_buttonNext)
	{
		navigateNext();
	}
	else if (context == m_buttonServices)
	{
		IGNORE_RETURN(CuiActionManager::performAction(CuiActions::service, Unicode::emptyString));
	}
	else if (context == m_buttonBug)
	{
		IGNORE_RETURN(CuiActionManager::performAction(CuiActions::bugReport, Unicode::emptyString));
	}
	else if (context == m_buttonReportPlayer)
	{
		IGNORE_RETURN(CuiActionManager::performAction(CuiActions::harassmentMessage, Unicode::emptyString));
	}
	else if (context == m_buttonReload && m_buttonReload != 0)
	{
		CuiKnowledgeBaseManager::reloadData();
		populateTopicTree();
		if (!m_currentPageName.empty())
		{
			loadPage(m_currentPageName);
		}
	}
	else
	{
		std::string linkTarget;
		context->GetPropertyNarrow(KBLinkTargetProperty, linkTarget);
		if (!linkTarget.empty())
		{
			loadPage(linkTarget);
			return;
		}

		std::string kbCommand;
		context->GetPropertyNarrow(KBCommandProperty, kbCommand);
		if (!kbCommand.empty())
		{
			// Strip leading '/' if present, then split into command name and params
			std::string cmd = kbCommand;
			if (!cmd.empty() && cmd[0] == '/')
				cmd.erase(cmd.begin());
			std::string::size_type const spacePos = cmd.find(' ');
			std::string const commandName = cmd.substr(0, spacePos);
			Unicode::String const commandParams = (spacePos != std::string::npos)
				? Unicode::narrowToWide(cmd.substr(spacePos + 1))
				: Unicode::emptyString;
			ClientCommandQueue::enqueueCommand(commandName, NetworkId::cms_invalid, commandParams);
		}
	}
}

//----------------------------------------------------------------------

void SwgCuiHolocron::OnGenericSelectionChanged(UIWidget * context)
{
	if (context == m_treeTopics && !m_syncingTree)
	{
		int const selectedRow = m_treeTopics->GetLastSelectedRow();
		UIDataSourceContainer const * const dsc = m_treeTopics->GetDataSourceContainerAtRow(selectedRow);

		if (dsc)
		{
			std::string nodeName;
			dsc->GetPropertyNarrow(KBNodeNameProperty, nodeName);

			if (!nodeName.empty())
			{
				loadPage(nodeName);
			}
		}
	}
}

//----------------------------------------------------------------------

void SwgCuiHolocron::loadPage(const std::string & pageName)
{
	CuiKnowledgeBaseManager::BaseKBNode * const node = CuiKnowledgeBaseManager::findNode(pageName);

	if (node)
	{
		displayPage(node);

		syncTreeSelection(pageName);

		m_currentPageName = pageName;

		// Truncate forward history if navigating to a new page
		if (m_navigationIndex < static_cast<int>(m_navigationHistory.size()) - 1)
		{
			m_navigationHistory.erase(
				m_navigationHistory.begin() + m_navigationIndex + 1,
				m_navigationHistory.end()
			);
		}

		m_navigationHistory.push_back(pageName);
		m_navigationIndex = static_cast<int>(m_navigationHistory.size()) - 1;

		updateNavigationButtons();
	}
	else
	{
		DEBUG_WARNING(true, ("SwgCuiHolocron: Page not found: %s", pageName.c_str()));
	}
}

//----------------------------------------------------------------------

void SwgCuiHolocron::setActivePage(const std::string & pageName)
{
	loadPage(pageName);
}

//----------------------------------------------------------------------

void SwgCuiHolocron::populateTopicTree()
{
	if (!m_treeTopics)
		return;

	UIDataSourceContainer * const mainDsc = NON_NULL(m_treeTopics->GetDataSourceContainer());
	mainDsc->Attach(0);
	m_treeTopics->SetDataSourceContainer(0);
	mainDsc->Clear();

	CuiKnowledgeBaseManager::BaseKBNode * const root = CuiKnowledgeBaseManager::getRoot();
	if (root)
	{
		for (std::vector<CuiKnowledgeBaseManager::BaseKBNode *>::const_iterator it = root->m_children.begin();
		     it != root->m_children.end(); ++it)
		{
			populateDataSourceRecursive(mainDsc, *it);
		}
	}

	m_treeTopics->SetDataSourceContainer(mainDsc);
	mainDsc->Detach(0);
}

//----------------------------------------------------------------------

void SwgCuiHolocron::populateDataSourceRecursive(UIDataSourceContainer * parentDsc, CuiKnowledgeBaseManager::BaseKBNode * node)
{
	if (!node || !parentDsc)
		return;

	if (node->m_type != CuiKnowledgeBaseManager::s_pageType)
		return;

	CuiKnowledgeBaseManager::PageKBNode * const pageNode = static_cast<CuiKnowledgeBaseManager::PageKBNode *>(node);

	Unicode::String title;
	if (pageNode->m_string.isValid())
	{
		title = pageNode->m_string.localize();
	}
	else
	{
		title = Unicode::narrowToWide(node->m_name);
	}

	UIDataSourceContainer * const nodeDsc = new UIDataSourceContainer;
	nodeDsc->SetProperty(UITreeView::DataProperties::Text, title);
	nodeDsc->SetPropertyNarrow(KBNodeNameProperty, node->m_name);
	nodeDsc->SetPropertyBoolean(UITreeView::DataProperties::Selectable, true);
	nodeDsc->SetPropertyBoolean(UITreeView::DataProperties::Expanded, false);

	parentDsc->AddChild(nodeDsc);

	for (std::vector<CuiKnowledgeBaseManager::BaseKBNode *>::const_iterator it = node->m_children.begin();
	     it != node->m_children.end(); ++it)
	{
		populateDataSourceRecursive(nodeDsc, *it);
	}
}

//----------------------------------------------------------------------

void SwgCuiHolocron::displayPage(CuiKnowledgeBaseManager::BaseKBNode * node)
{
	if (!node)
		return;

	clearContent();

	if (node->m_type == CuiKnowledgeBaseManager::s_pageType)
	{
		CuiKnowledgeBaseManager::PageKBNode * const pageNode = static_cast<CuiKnowledgeBaseManager::PageKBNode *>(node);
		if (pageNode->m_string.isValid())
		{
			m_entryTitle->SetLocalText(pageNode->m_string.localize());
		}
		else
		{
			m_entryTitle->SetLocalText(Unicode::narrowToWide(node->m_name));
		}
	}

	Unicode::String contentText;

	for (std::vector<CuiKnowledgeBaseManager::BaseKBNode *>::const_iterator it = node->m_children.begin();
	     it != node->m_children.end(); ++it)
	{
		CuiKnowledgeBaseManager::BaseKBNode * const child = *it;

		if (child->m_type == CuiKnowledgeBaseManager::s_stringType)
		{
			CuiKnowledgeBaseManager::StringKBNode * const stringNode = static_cast<CuiKnowledgeBaseManager::StringKBNode *>(child);
			if (stringNode->m_string.isValid())
			{
				contentText += stringNode->m_string.localize();
				contentText += Unicode::narrowToWide("\n\n");
			}
		}
		else if (child->m_type == CuiKnowledgeBaseManager::s_imageType)
		{
			CuiKnowledgeBaseManager::ImageKBNode * const imageNode = static_cast<CuiKnowledgeBaseManager::ImageKBNode *>(child);
			if (!imageNode->m_path.empty())
			{
				m_imageSample->SetVisible(true);
				IGNORE_RETURN(m_imageSample->SetSourceResource(Unicode::narrowToWide(imageNode->m_path)));
			}
		}
		else if (child->m_type == CuiKnowledgeBaseManager::s_linkButtonType)
		{
			CuiKnowledgeBaseManager::LinkButtonKBNode * const linkNode = static_cast<CuiKnowledgeBaseManager::LinkButtonKBNode *>(child);

			UIButton * const linkButton = safe_cast<UIButton *>(m_buttonSample->DuplicateObject());
			NOT_NULL(linkButton);
			linkButton->SetName(cms_linkButton);
			linkButton->SetPropertyNarrow(KBLinkTargetProperty, linkNode->m_link);

			m_entryComp->AddChild(linkButton);

			// Copy the already-resolved ButtonStyle directly from the template
			// (m_buttonSample is always in the tree, so its style is always linked)
			UIButtonStyle * const templateStyle = const_cast<UIButtonStyle *>(m_buttonSample->GetButtonStyle());
			if (templateStyle)
				linkButton->SetStyle(templateStyle);

			// SetText() calls CreateLocalizedString() which resolves @table:key directly
			linkButton->SetText(Unicode::narrowToWide(linkNode->m_string));

			linkButton->SetVisible(true);
			registerMediatorObject(*linkButton, true);
		}
		else if (child->m_type == CuiKnowledgeBaseManager::s_commandButtonType)
		{
			CuiKnowledgeBaseManager::CommandButtonKBNode * const cmdNode =
				static_cast<CuiKnowledgeBaseManager::CommandButtonKBNode *>(child);

			UIButton * const cmdButton = safe_cast<UIButton *>(m_buttonSample->DuplicateObject());
			NOT_NULL(cmdButton);
			cmdButton->SetName(cms_linkButton);
			cmdButton->SetPropertyNarrow(KBCommandProperty, cmdNode->m_command);

			m_entryComp->AddChild(cmdButton);

			UIButtonStyle * const templateStyle = const_cast<UIButtonStyle *>(m_buttonSample->GetButtonStyle());
			if (templateStyle)
				cmdButton->SetStyle(templateStyle);

			cmdButton->SetText(Unicode::narrowToWide(cmdNode->m_string));
			cmdButton->SetVisible(true);
			registerMediatorObject(*cmdButton, true);
		}
	}

	if (m_entryText)
	{
		m_entryText->SetLocalText(contentText);
	}

	// Force a layout repack by ensuring m_entryComp always has a child added.
	// Without this, pages that lack a LinkButton never trigger AddChild,
	// and the text content fails to render.
	if (m_buttonSample && m_entryComp)
	{
		UIButton * const spacer = safe_cast<UIButton *>(m_buttonSample->DuplicateObject());
		if (spacer)
		{
			spacer->SetVisible(false);
			spacer->SetSize(UISize(0, 0));
			spacer->SetName(cms_linkButton);
			m_entryComp->AddChild(spacer);
		}
	}
}

//----------------------------------------------------------------------

void SwgCuiHolocron::clearContent()
{
	if (m_entryText)
		m_entryText->Clear();
	if (m_entryTitle)
		m_entryTitle->Clear();
	if (m_imageSample)
		m_imageSample->SetVisible(false);

	// Remove dynamically created link buttons from entrycomp
	if (m_entryComp)
	{
		UIBaseObject * linkBtn = m_entryComp->GetChild(cms_linkButton.c_str());
		while (linkBtn)
		{
			m_entryComp->RemoveChild(linkBtn);
			linkBtn = m_entryComp->GetChild(cms_linkButton.c_str());
		}
	}
}

//----------------------------------------------------------------------

void SwgCuiHolocron::navigateBack()
{
	if (m_navigationIndex > 0)
	{
		--m_navigationIndex;
		std::string const & pageName = m_navigationHistory[static_cast<size_t>(m_navigationIndex)];

		CuiKnowledgeBaseManager::BaseKBNode * const node = CuiKnowledgeBaseManager::findNode(pageName);
		if (node)
		{
			displayPage(node);
			syncTreeSelection(pageName);
			m_currentPageName = pageName;
		}

		updateNavigationButtons();
	}
}

//----------------------------------------------------------------------

void SwgCuiHolocron::navigateNext()
{
	if (m_navigationIndex < static_cast<int>(m_navigationHistory.size()) - 1)
	{
		++m_navigationIndex;
		std::string const & pageName = m_navigationHistory[static_cast<size_t>(m_navigationIndex)];

		CuiKnowledgeBaseManager::BaseKBNode * const node = CuiKnowledgeBaseManager::findNode(pageName);
		if (node)
		{
			displayPage(node);
			syncTreeSelection(pageName);
			m_currentPageName = pageName;
		}

		updateNavigationButtons();
	}
}

//----------------------------------------------------------------------

void SwgCuiHolocron::syncTreeSelection(const std::string & pageName)
{
	if (!m_treeTopics)
		return;

	UIDataSourceContainer * const rootDsc = m_treeTopics->GetDataSourceContainer();
	if (!rootDsc)
		return;

	// DFS over datasource containers to find the one matching pageName
	UIDataSourceContainer * targetDsc = 0;
	std::vector<UIDataSourceContainer *> stack;
	stack.push_back(rootDsc);

	while (!stack.empty())
	{
		UIDataSourceContainer * cur = stack.back();
		stack.pop_back();

		std::string kbName;
		cur->GetPropertyNarrow(KBNodeNameProperty, kbName);
		if (!kbName.empty() && kbName == pageName)
		{
			targetDsc = cur;
			break;
		}

		unsigned long const childCount = cur->GetChildCount();
		for (unsigned long i = 0; i < childCount; ++i)
		{
			UIDataSourceBase * const child = cur->GetChildByPositionLinear(i);
			if (child && child->IsA(TUIDataSourceContainer))
				stack.push_back(static_cast<UIDataSourceContainer *>(child));
		}
	}

	if (!targetDsc)
		return;

	int row = -1;
	UITreeView::DataNode * const dataNode = m_treeTopics->FindDataNodeByDataSource(*targetDsc, row);
	if (!dataNode)
		return;

	// Expand parents first — this inserts visible rows and invalidates the row index
	m_treeTopics->ExpandParentNodes(*dataNode);

	// Re-query row after expansion since visible row indices have shifted
	m_treeTopics->FindDataNodeByDataSource(*targetDsc, row);
	if (row >= 0)
	{
		m_syncingTree = true;
		m_treeTopics->SelectRow(row);
		m_treeTopics->ScrollToRow(row);
		m_syncingTree = false;
	}
}

//----------------------------------------------------------------------

void SwgCuiHolocron::updateNavigationButtons()
{
	if (m_buttonBack)
		m_buttonBack->SetEnabled(m_navigationIndex > 0);

	if (m_buttonNext)
		m_buttonNext->SetEnabled(m_navigationIndex < static_cast<int>(m_navigationHistory.size()) - 1);
}

//----------------------------------------------------------------------

SwgCuiHolocron * SwgCuiHolocron::createInto(UIPage * parent)
{
	UIPage * const dupe = UIPage::DuplicateInto(*parent, "/PDA.help");

	if (!dupe)
	{
		DEBUG_WARNING(true, ("[Holocron] createInto: DuplicateInto failed for /PDA.help"));
		return 0;
	}

	return new SwgCuiHolocron(*dupe);
}

//======================================================================
