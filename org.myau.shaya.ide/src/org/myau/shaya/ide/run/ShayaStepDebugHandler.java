package org.myau.shaya.ide.run;

import org.eclipse.core.commands.AbstractHandler;
import org.eclipse.core.commands.ExecutionEvent;
import org.eclipse.core.commands.ExecutionException;
import org.eclipse.core.expressions.IEvaluationContext;
import org.eclipse.core.resources.IFile;
import org.eclipse.debug.core.ILaunchManager;
import org.eclipse.debug.ui.DebugUITools;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.ui.IEditorPart;
import org.eclipse.ui.ISources;
import org.eclipse.ui.handlers.HandlerUtil;
import org.myau.shaya.ide.editor.ShayaEditor;
import org.myau.shaya.ide.launch.ShayaLaunchShortcut;
import org.myau.shaya.ide.toolchain.ShayaToolchain;

/**
 * ALG → Step Debug: Eclipse Debug Framework + SHAYDBG protocol.
 */
public class ShayaStepDebugHandler extends AbstractHandler {

	@Override
	public void setEnabled(Object evaluationContext) {
		boolean enable = false;
		if (evaluationContext instanceof IEvaluationContext) {
			Object active = ((IEvaluationContext) evaluationContext).getVariable(ISources.ACTIVE_EDITOR_NAME);
			if (active instanceof ShayaEditor) {
				String name = ((ShayaEditor) active).getEditorInput() != null
						? ((ShayaEditor) active).getEditorInput().getName() : null;
				String eng = ShayaToolchain.engineIdForName(name);
				enable = eng != null && ShayaToolchain.supportsStepDebugUi(eng);
			}
		}
		setBaseEnabled(enable);
	}

	@Override
	public Object execute(ExecutionEvent event) throws ExecutionException {
		ShayaSourceResolver.ResolvedSource src = ShayaSourceResolver.resolveSource(event);
		if (src == null) {
			MessageDialog.openInformation(HandlerUtil.getActiveShell(event), "ALG Step Debug",
					"Open a ALG source file first.");
			return null;
		}
		String engine = ShayaToolchain.engineIdFor(src.file);
		if (!ShayaToolchain.supportsStepDebugUi(engine)) {
			MessageDialog.openInformation(HandlerUtil.getActiveShell(event), "ALG Step Debug",
					ShayaToolchain.stepDebugRefuseMessage(engine));
			return null;
		}
		IFile wf = src.workspaceFile;
		if (wf == null || !wf.exists()) {
			MessageDialog.openInformation(HandlerUtil.getActiveShell(event), "ALG Step Debug",
					"Step Debug needs a workspace file (File → Open external is not enough).\n"
							+ "Import the file into a project, or use examples under the workspace.");
			return null;
		}
		IEditorPart editor = HandlerUtil.getActiveEditor(event);
		if (editor != null && editor.isDirty()) {
			editor.doSave(null);
		}
		try {
			DebugUITools.launch(ShayaLaunchShortcut.findOrCreate(wf), ILaunchManager.DEBUG_MODE);
		} catch (Exception e) {
			MessageDialog.openError(HandlerUtil.getActiveShell(event), "ALG Step Debug",
					e.getMessage() != null ? e.getMessage() : String.valueOf(e));
		}
		return null;
	}
}
