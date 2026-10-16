# -*- coding: utf-8 -*-
"""Escape hatch: run IronPython inside Revit."""

from .utils import Context, format_response


def register_code_execution_tools(mcp, revit_get, revit_post, revit_image):
    """Register execute_revit_code."""
    del revit_get, revit_image  # not needed by this tool

    @mcp.tool()
    async def execute_revit_code(
        code: str, description: str = "Code execution", timeout_seconds: float = 30.0, ctx: Context = None
    ) -> str:
        """Run IronPython 2.7 code inside Revit and return what it prints.

        Only use this when no dedicated tool can do the job. The code runs
        inside a single transaction that is committed on success and rolled
        back on error, so do not start your own Transaction.

        Available names: ``doc`` (active Document), ``DB`` (Autodesk.Revit.DB),
        ``revit`` (pyRevit helpers), ``System``, ``clr``, and ``print`` (its
        output is returned to you).

        IronPython 2.7 rules:
        * no f-strings; use "{}".format(...)
        * Revit stores lengths in feet; divide millimeters by 304.8
        * build element IDs as DB.ElementId(System.Int64(n)); a bare int is
          ambiguous in Revit 2027
        * some elements lack ``.Name``; read it defensively, e.g.
          getattr(el, "Name", None) or the ALL_MODEL_TYPE_NAME parameter
        * check doc.GetElement(...) for None before using the result

        Example:
            walls = DB.FilteredElementCollector(doc) \\
                .OfCategory(DB.BuiltInCategory.OST_Walls) \\
                .WhereElementIsNotElementType().ToElements()
            print("walls: {}".format(len(walls)))

        Args:
            code: IronPython source to execute.
            description: Short label; it becomes the transaction name shown
                in Revit's Undo menu.
            timeout_seconds: How long to wait for Revit (default 30, max 600).
                Raise it for slow work such as opening a large model in the
                background (opening a 75 MB model took about 70 s).
        """
        if ctx:
            await ctx.info("Running Revit code: {}".format(description))
        payload = {"code": code, "description": description}
        timeout = max(5.0, min(float(timeout_seconds), 600.0))
        return format_response(await revit_post("/execute_code/", payload, ctx, timeout=timeout))
