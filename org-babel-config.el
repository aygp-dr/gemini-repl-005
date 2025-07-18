;;; org-babel-config.el --- Configuration for org-babel shell execution

;; Enable shell and bash execution in org-babel
(require 'org)
(require 'ob-shell)

;; Add shell and bash to the list of languages org-babel can execute
(org-babel-do-load-languages
 'org-babel-load-languages
 '((shell . t)
   (bash . t)
   (python . t)
   (emacs-lisp . t)))

;; Security: Don't ask for confirmation when executing code blocks
;; (Only use this if you trust the code in your org files!)
(setq org-confirm-babel-evaluate nil)

;; Custom function to execute shell blocks with better error handling
(defun org-babel-execute:bash (body params)
  "Execute a block of Bash code with org-babel.
This extends the default shell execution with better error handling."
  (let ((org-babel-sh-command "bash"))
    (org-babel-execute:shell body params)))

;; Alternative: Execute shell blocks and capture both stdout and stderr
(defun my/org-babel-execute-shell-with-stderr (body params)
  "Execute shell code and capture both stdout and stderr."
  (let* ((tmp-stderr (make-temp-file "babel-shell-stderr-"))
         (full-body (concat body " 2>" tmp-stderr))
         (result (org-babel-execute:shell full-body params))
         (stderr (with-temp-buffer
                   (insert-file-contents tmp-stderr)
                   (buffer-string))))
    (delete-file tmp-stderr)
    (if (string-empty-p stderr)
        result
      (concat result "\n\nSTDERR:\n" stderr))))

;; Header argument defaults for shell blocks
(setq org-babel-default-header-args:shell
      '((:results . "output")
        (:exports . "both")
        (:wrap . "example")))

(setq org-babel-default-header-args:bash
      '((:results . "output")
        (:exports . "both")
        (:wrap . "example")
        (:shebang . "#!/bin/bash")))

;; Function to tangle with comments for all blocks
(defun my/org-babel-tangle-with-comments ()
  "Tangle the current org file with comments enabled for all blocks."
  (interactive)
  (let ((org-babel-default-header-args 
         (append org-babel-default-header-args
                 '((:comments . "both")
                   (:mkdirp . "yes")))))
    (org-babel-tangle)))

;; Keybindings for convenience
(with-eval-after-load 'org
  (define-key org-mode-map (kbd "C-c C-v t") 'my/org-babel-tangle-with-comments)
  (define-key org-mode-map (kbd "C-c C-v x") 'org-babel-execute-src-block))

(provide 'org-babel-config)
;;; org-babel-config.el ends here