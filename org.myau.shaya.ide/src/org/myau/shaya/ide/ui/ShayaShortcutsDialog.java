package org.myau.shaya.ide.ui;

import org.eclipse.jface.dialogs.Dialog;
import org.eclipse.jface.dialogs.IDialogConstants;
import org.eclipse.swt.SWT;
import org.eclipse.swt.custom.StyledText;
import org.eclipse.swt.graphics.Font;
import org.eclipse.swt.graphics.FontData;
import org.eclipse.swt.layout.GridData;
import org.eclipse.swt.layout.GridLayout;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.swt.widgets.Control;
import org.eclipse.swt.widgets.Shell;

/** Scrollable keyboard shortcuts cheat sheet. */
public class ShayaShortcutsDialog extends Dialog {

	static final String TEXT = ""
			+ "ALG / SCHOOLALGOL — горячие клавиши\n\n"
			+ "Запуск\n"
			+ "  Ctrl+Alt+R        Run (.alg)\n"
			+ "  Ctrl+Alt+C        Check (lex + parse)\n"
			+ "  Ctrl+Alt+L        Run Last\n"
			+ "  Run As → ALG Application\n"
			+ "  ALG → Recent → Open / Clear Recent\n"
			+ "  ALG → Welcome…\n\n"
			+ "Правка\n"
			+ "  F3 / Ctrl+Click   Go to Declaration\n"
			+ "  Ctrl+O            Quick Outline\n"
			+ "  Ctrl+Shift+G      Find References\n"
			+ "  Alt+Shift+R       Rename…\n"
			+ "  Ctrl+Shift+F      Reindent\n"
			+ "  Ctrl+/            Toggle Comment (|)\n"
			+ "  Ctrl+Shift+P      Go to Matching Block\n"
			+ "  Ctrl+Shift+E      Expand Selection to Block\n"
			+ "  Ctrl+D            Duplicate Lines\n"
			+ "  Alt+↑ / Alt+↓     Move Lines Up / Down\n"
			+ "  Ctrl+Alt+J        Join Lines\n"
			+ "  Alt+Shift+S       Sort Lines\n"
			+ "  Ctrl+Space        Templates + keywords (RU/EN)\n"
			+ "  Enter             Auto-indent after begin/if/loop / нач/если/нц…\n"
			+ "  Console           клик file:line / строка N → исходник\n\n"
			+ "Проект\n"
			+ "  File → New → Project → ALG Project\n"
			+ "  File → New → ALG → ALG Hello\n"
			+ "  Window → Perspective → ALG\n"
			+ "  Preferences → ALG (Toolchain home)\n"
			+ "  .alg → SCHOOLALGOL\n";

	private Font mono;

	public ShayaShortcutsDialog(Shell parentShell) {
		super(parentShell);
		setShellStyle(getShellStyle() | SWT.RESIZE | SWT.MAX);
	}

	@Override
	protected void configureShell(Shell newShell) {
		super.configureShell(newShell);
		newShell.setText("ALG Shortcuts");
		newShell.setMinimumSize(480, 420);
	}

	@Override
	protected Control createDialogArea(Composite parent) {
		Composite area = (Composite) super.createDialogArea(parent);
		area.setLayout(new GridLayout(1, false));

		StyledText text = new StyledText(area, SWT.BORDER | SWT.V_SCROLL | SWT.H_SCROLL | SWT.READ_ONLY | SWT.MULTI | SWT.WRAP);
		GridData gd = new GridData(SWT.FILL, SWT.FILL, true, true);
		gd.widthHint = 520;
		gd.heightHint = 420;
		text.setLayoutData(gd);
		text.setText(TEXT);
		text.setEditable(false);
		FontData[] fds = text.getFont().getFontData();
		for (FontData fd : fds) {
			fd.setHeight(Math.max(9, fd.getHeight()));
			fd.setName("Consolas");
		}
		mono = new Font(parent.getDisplay(), fds);
		text.setFont(mono);
		return area;
	}

	@Override
	protected void createButtonsForButtonBar(Composite parent) {
		createButton(parent, IDialogConstants.OK_ID, IDialogConstants.CLOSE_LABEL, true);
	}

	@Override
	public boolean close() {
		if (mono != null && !mono.isDisposed()) {
			mono.dispose();
			mono = null;
		}
		return super.close();
	}
}
