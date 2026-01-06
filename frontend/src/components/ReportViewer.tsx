'use client';

import { useRef } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';

interface ReportViewerProps {
  isOpen: boolean;
  onClose: () => void;
  htmlContent: string | null;
  pdfUrl: string | null;
}

export function ReportViewer({ isOpen, onClose, htmlContent }: ReportViewerProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null);

  const handlePrint = () => {
    if (iframeRef.current?.contentWindow) {
      iframeRef.current.contentWindow.print();
    }
  };

  const handleDownloadHtml = () => {
    if (htmlContent) {
      const blob = new Blob([htmlContent], { type: 'text/html' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'cable_ampacity_report.html';
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl h-[80vh]">
        <DialogHeader>
          <DialogTitle>Engineering Report</DialogTitle>
        </DialogHeader>

        <div className="flex-1 overflow-hidden mt-4 h-full">
            {htmlContent ? (
              <iframe
              ref={iframeRef}
                srcDoc={htmlContent}
                className="w-full h-full border rounded-lg"
                title="Report Preview"
              />
            ) : (
              <div className="flex items-center justify-center h-full text-muted-foreground">
                No report content available
              </div>
            )}
              </div>

        <div className="flex justify-end gap-2 mt-4">
          {htmlContent && (
            <>
              <Button variant="outline" onClick={handleDownloadHtml}>
              Download HTML
            </Button>
              <Button onClick={handlePrint}>
                Print / Save as PDF
            </Button>
            </>
          )}
          <Button variant="secondary" onClick={onClose}>
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
