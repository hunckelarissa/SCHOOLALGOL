package org.myau.shaya.ide.debug;

import org.eclipse.core.runtime.CoreException;
import org.eclipse.debug.core.model.IBreakpoint;
import org.eclipse.swt.SWT;
import org.eclipse.swt.layout.GridData;
import org.eclipse.swt.layout.GridLayout;
import org.eclipse.swt.widgets.Button;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.swt.widgets.Control;
import org.eclipse.swt.widgets.Label;
import org.eclipse.swt.widgets.Text;
import org.eclipse.ui.dialogs.PropertyPage;

/**
 * Properties: Condition + Hit Count + Log message for ALG line breakpoints.
 */
public class ShayaBreakpointPropertyPage extends PropertyPage {

	private Button enabledBtn;
	private Button suspendBtn;
	private Button conditionEnabledBtn;
	private Text conditionText;
	private Text hitCountText;
	private Text logMessageText;
	private ShayaLineBreakpoint breakpoint;

	@Override
	protected Control createContents(Composite parent) {
		IBreakpoint bp = getBreakpoint();
		if (!(bp instanceof ShayaLineBreakpoint)) {
			Label l = new Label(parent, SWT.NONE);
			l.setText("Not a ALG breakpoint");
			return l;
		}
		breakpoint = (ShayaLineBreakpoint) bp;
		Composite root = new Composite(parent, SWT.NONE);
		root.setLayout(new GridLayout(2, false));

		enabledBtn = new Button(root, SWT.CHECK);
		enabledBtn.setText("Enabled");
		enabledBtn.setLayoutData(new GridData(SWT.FILL, SWT.CENTER, true, false, 2, 1));

		suspendBtn = new Button(root, SWT.CHECK);
		suspendBtn.setText("Suspend execution");
		suspendBtn.setLayoutData(new GridData(SWT.FILL, SWT.CENTER, true, false, 2, 1));
		suspendBtn.setToolTipText(
				"Uncheck and set Log message for a logpoint (no stop)");

		conditionEnabledBtn = new Button(root, SWT.CHECK);
		conditionEnabledBtn.setText("Enable condition");
		conditionEnabledBtn.setLayoutData(new GridData(SWT.FILL, SWT.CENTER, true, false, 2, 1));

		Label cLab = new Label(root, SWT.NONE);
		cLab.setText("Condition:");
		conditionText = new Text(root, SWT.BORDER);
		conditionText.setLayoutData(new GridData(SWT.FILL, SWT.CENTER, true, false));
		conditionText.setToolTipText("ALG expression, e.g. x > 10");

		Label hLab = new Label(root, SWT.NONE);
		hLab.setText("Hit count:");
		hitCountText = new Text(root, SWT.BORDER);
		hitCountText.setLayoutData(new GridData(SWT.FILL, SWT.CENTER, true, false));
		hitCountText.setToolTipText("0 = every hit; N = stop on N-th hit");

		Label logLab = new Label(root, SWT.NONE);
		logLab.setText("Log message:");
		logMessageText = new Text(root, SWT.BORDER);
		logMessageText.setLayoutData(new GridData(SWT.FILL, SWT.CENTER, true, false));
		logMessageText.setToolTipText("Template: x={x}. {{ and }} are literal braces");

		try {
			enabledBtn.setSelection(breakpoint.isEnabled());
			suspendBtn.setSelection(breakpoint.isSuspend());
			conditionEnabledBtn.setSelection(breakpoint.isConditionEnabled());
			conditionText.setText(breakpoint.getCondition());
			hitCountText.setText(String.valueOf(breakpoint.getHitCount()));
			logMessageText.setText(breakpoint.getLogMessage());
		} catch (CoreException e) {
			// ignore
		}
		return root;
	}

	private IBreakpoint getBreakpoint() {
		Object el = getElement();
		if (el instanceof IBreakpoint) {
			return (IBreakpoint) el;
		}
		if (el instanceof org.eclipse.core.runtime.IAdaptable) {
			return ((org.eclipse.core.runtime.IAdaptable) el).getAdapter(IBreakpoint.class);
		}
		return null;
	}

	@Override
	public boolean performOk() {
		if (breakpoint == null) {
			return true;
		}
		try {
			breakpoint.setEnabled(enabledBtn.getSelection());
			breakpoint.setSuspend(suspendBtn.getSelection());
			breakpoint.setConditionEnabled(conditionEnabledBtn.getSelection());
			breakpoint.setCondition(conditionText.getText());
			breakpoint.setLogMessage(logMessageText.getText());
			int hit = 0;
			try {
				hit = Integer.parseInt(hitCountText.getText().trim());
			} catch (NumberFormatException e) {
				hit = 0;
			}
			breakpoint.setHitCount(hit);
			String msg = breakpoint.getLogMessage().trim();
			if (!msg.isEmpty() && !breakpoint.isSuspend()) {
				breakpoint.getMarker().setAttribute(
						org.eclipse.core.resources.IMarker.MESSAGE,
						"ALG logpoint: " + msg);
			}
		} catch (CoreException e) {
			return false;
		}
		return true;
	}
}
