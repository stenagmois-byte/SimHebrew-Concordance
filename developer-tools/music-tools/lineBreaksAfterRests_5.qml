import QtQuick 2.0
import MuseScore 3.0

MuseScore {

    title: "Add Line Breaks After Rests (v5)"

    requiresScore: true
    
    onRun: {
        var sel = curScore.selection.elements;
        var selezione = [];

        for (var i=0; i<sel.length; i++)
            if (sel[i].type == Element.REST)
                selezione.push(sel[i]);

        for (var i=0; i<selezione.length; i++)
        {
                curScore.startCmd();
                curScore.selection.select(selezione[i], false);
                curScore.endCmd(); 

                curScore.startCmd();
                cmd("system-break");
                curScore.endCmd();                                       
            }

        quit();
    }
}
