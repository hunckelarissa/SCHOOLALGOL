package org.myau.shaya.ide.ui;

import org.eclipse.ui.IFolderLayout;
import org.eclipse.ui.IPageLayout;
import org.eclipse.ui.IPerspectiveFactory;

/**
 * ALG perspective: Explorer + Editor + Console + Problems + Outline.
 */
public class ShayaPerspectiveFactory implements IPerspectiveFactory {

	public static final String ID = "org.myau.shaya.ide.perspective";

	@Override
	public void createInitialLayout(IPageLayout layout) {
		String editor = layout.getEditorArea();

		IFolderLayout left = layout.createFolder("left", IPageLayout.LEFT, 0.22f, editor);
		left.addView(IPageLayout.ID_PROJECT_EXPLORER);

		IFolderLayout bottom = layout.createFolder("bottom", IPageLayout.BOTTOM, 0.72f, editor);
		bottom.addView("org.eclipse.ui.console.ConsoleView");
		bottom.addView(IPageLayout.ID_PROBLEM_VIEW);

		IFolderLayout right = layout.createFolder("right", IPageLayout.RIGHT, 0.75f, editor);
		right.addView(IPageLayout.ID_OUTLINE);

		layout.addShowViewShortcut(IPageLayout.ID_PROJECT_EXPLORER);
		layout.addShowViewShortcut("org.eclipse.ui.console.ConsoleView");
		layout.addShowViewShortcut(IPageLayout.ID_PROBLEM_VIEW);
		layout.addShowViewShortcut(IPageLayout.ID_OUTLINE);
		layout.addNewWizardShortcut("org.myau.shaya.ide.wizards.newProject");
		layout.addNewWizardShortcut("org.myau.shaya.ide.wizards.newHello");
	}
}
