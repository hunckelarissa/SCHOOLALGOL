package org.myau.shaya.ide.editor;

import org.eclipse.jface.action.ContributionItem;
import org.eclipse.swt.SWT;
import org.eclipse.swt.custom.CLabel;
import org.eclipse.swt.widgets.Composite;

/** Compact capability flags on the status line; details live in the control tooltip. */
final class ShayaEngineStatusContribution extends ContributionItem {

	private String text = "";
	private String tip = "";
	private CLabel label;

	ShayaEngineStatusContribution() {
		super("org.myau.shaya.ide.engineStatus");
	}

	void setText(String value) {
		text = value != null ? value : "";
		if (label != null && !label.isDisposed()) {
			label.setText(text);
			label.getParent().layout();
		}
	}

	void setToolTipText(String value) {
		tip = value != null ? value : "";
		if (label != null && !label.isDisposed()) {
			label.setToolTipText(tip);
		}
	}

	@Override
	public void fill(Composite parent) {
		label = new CLabel(parent, SWT.NONE);
		label.setText(text);
		label.setToolTipText(tip);
	}
}
