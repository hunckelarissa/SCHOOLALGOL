package org.myau.shaya.ide.editor;

import org.eclipse.ui.editors.text.TextFileDocumentProvider;

/**
 * Workspace files + File→Open (URI / FileStore).
 * Do not use FileDocumentProvider — it ignores external opens (no color, no save path).
 */
public class ShayaDocumentProvider extends TextFileDocumentProvider {
}
