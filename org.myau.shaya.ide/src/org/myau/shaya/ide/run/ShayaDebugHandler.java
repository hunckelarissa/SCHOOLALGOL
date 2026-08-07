package org.myau.shaya.ide.run;

import org.eclipse.core.commands.AbstractHandler;
import org.eclipse.core.commands.ExecutionEvent;
import org.eclipse.core.commands.ExecutionException;
import org.eclipse.core.expressions.IEvaluationContext;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.ui.IEditorPart;
import org.eclipse.ui.ISources;
import org.eclipse.ui.handlers.HandlerUtil;
import org.myau.shaya.ide.editor.ShayaEditor;
import org.myau.shaya.ide.toolchain.ShayaToolchain;

/**
 * CLI Debug — SCHOOLALGOL не поддерживает; показывается refuse dialog.
 */
public class ShayaDebugHandler extends AbstractHandler {

	@Override
	public void setEnabled(Object evaluationContext) {
		boolean enable = false;
		if (evaluationContext instanceof IEvaluationContext) {
			Object active = ((IEvaluationContext) evaluationContext).getVariable(ISources.ACTIVE_EDITOR_NAME);
			if (active instanceof ShayaEditor) {
				String name = ((ShayaEditor) active).getEditorInput() != null
						? ((ShayaEditor) active).getEditorInput().getName() : null;
				String eng = ShayaToolchain.engineIdForName(name);
				enable = eng != null && ShayaToolchain.supportsDebug(eng);
			}
		}
		setBaseEnabled(enable);
	}

	@Override
	public Object execute(ExecutionEvent event) throws ExecutionException {
		ShayaSourceResolver.ResolvedSource src = ShayaSourceResolver.resolveSource(event);
		if (src == null) {
			MessageDialog.openWarning(HandlerUtil.getActiveShell(event), "ALG",
					"Open or select a ALG source (" + ShayaToolchain.extensionsHint() + ").");
			return null;
		}
		String engine = ShayaToolchain.engineIdFor(src.file);
		if (engine == null) {
			MessageDialog.openWarning(HandlerUtil.getActiveShell(event), "ALG",
					"Unknown ALG extension: " + src.file.getName());
			return null;
		}
		if (!ShayaToolchain.supportsDebug(engine)) {
			MessageDialog.openInformation(HandlerUtil.getActiveShell(event), "ALG Debug",
					ShayaToolchain.debugRefuseMessage(engine));
			return null;
		}
		IEditorPart editor = HandlerUtil.getActiveEditor(event);
		if (editor != null && editor.isDirty()) {
			editor.doSave(null);
		}
		ShayaLastLaunch.remember(ShayaLastLaunch.Mode.DEBUG, src);
		ShayaLauncher.debug(src.file, src.workspaceFile);
		return null;
	}
}
