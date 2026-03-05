//======================================================================
//
// SwgCuiHolocron.h
// Copyright Sony Online Entertainment
//
//======================================================================

#ifndef INCLUDED_SwgCuiHolocron_H
#define INCLUDED_SwgCuiHolocron_H

//======================================================================

#include "clientUserInterface/CuiMediator.h"
#include "clientUserInterface/CuiKnowledgeBaseManager.h"
#include "UIEventCallback.h"

class UIButton;
class UIDataSourceContainer;
class UIImage;
class UIPage;
class UIText;
class UITreeView;

//======================================================================

class SwgCuiHolocron : public CuiMediator, public UIEventCallback
{
public:
	explicit SwgCuiHolocron(UIPage & page);

	virtual void performActivate();
	virtual void performDeactivate();

	virtual void OnButtonPressed(UIWidget *context);
	virtual void OnGenericSelectionChanged(UIWidget *context);

	void loadPage(const std::string & pageName);
	void setActivePage(const std::string & pageName);

	static SwgCuiHolocron * createInto(UIPage * parent);

private:
	~SwgCuiHolocron();
	SwgCuiHolocron(const SwgCuiHolocron & rhs);
	SwgCuiHolocron & operator=(const SwgCuiHolocron & rhs);

	void populateTopicTree();
	void populateDataSourceRecursive(UIDataSourceContainer * parentDsc, CuiKnowledgeBaseManager::BaseKBNode * node);
	void displayPage(CuiKnowledgeBaseManager::BaseKBNode * node);
	void clearContent();
	void navigateBack();
	void navigateNext();
	void updateNavigationButtons();
	void syncTreeSelection(const std::string & pageName);

private:
	UITreeView *  m_treeTopics;
	UIText *      m_entryText;
	UIText *      m_entryTitle;
	UIText *      m_textInfo;
	UIPage *      m_entryComp;
	UIImage *     m_imageSample;
	UIButton *    m_buttonBack;
	UIButton *    m_buttonNext;
	UIButton *    m_buttonClose;
	UIButton *    m_buttonExit;
	UIButton *    m_buttonServices;
	UIButton *    m_buttonBug;
	UIButton *    m_buttonReportPlayer;
	UIButton *    m_buttonReload;
	UIButton *    m_buttonSample;
	UIText *      m_textSample;

	std::vector<std::string> m_navigationHistory;
	int m_navigationIndex;
	std::string m_currentPageName;
	bool m_syncingTree;
};

//======================================================================

#endif // INCLUDED_SwgCuiHolocron_H
