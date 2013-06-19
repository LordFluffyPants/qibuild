## Copyright (c) 2012, 2013 Aldebaran Robotics. All rights reserved.

## Use of this source code is governed by a BSD-style license that can be
## found in the COPYING file.

""" A Pythonic git API

"""
import os
import contextlib
import subprocess
import functools

from qisys import ui
import qisys
import qisys.command

class Git(object):
    """ The Git represent a git tree """
    def __init__(self, repo):
        """ :param repo: The path to the tree """
        self.repo = repo
        self._transaction = None

    def call(self, *args, **kwargs):
        """
        Call a git command

        :param args: The arguments of the command.
                     For instance ["frobnicate", "--spam=eggs"]

        :param kwargs: Will be passed to subprocess.check_call()
                       command, with the following changes:

           * if cwd is not given it will be self.repo instead
           * if env is not given it will be read from the config file
           * if raises is False, no exception will be raised if command
             fails, and a (retcode, output) tuple will be returned.
        """
        if not self._transaction:
            return self._call(*args, **kwargs)

        if not self._transaction.ok:
            # Do not run any more command if transaction failed:
            return

        # Force raises to False
        kwargs["raises"] = False
        (retcode, out) = self._call(*args, **kwargs)
        if retcode != 0:
            self._transaction.ok = False
            self._transaction.output += "git %s failed\n" % (" ".join(args))
            self._transaction.output += out
        return (retcode, out)


    def _call(self, *args, **kwargs):
        """ Helper for self.call """
        ui.debug("git", " ".join(args))
        if not "cwd" in kwargs.keys():
            kwargs["cwd"] = self.repo
        if not "quiet" in kwargs.keys():
            kwargs["quiet"] = False
        git = qisys.command.find_program("git", raises=True)
        cmd = [git]
        cmd.extend(args)
        raises = kwargs.get("raises")
        if raises is False:
            del kwargs["raises"]
            del kwargs["quiet"]
            process = subprocess.Popen(cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                **kwargs)
            out = process.communicate()[0]
            # Don't want useless blank lines
            out = out.rstrip("\n")
            ui.debug("out:", out)
            return (process.returncode, out)
        else:
            qisys.command.call(cmd, **kwargs)

    @contextlib.contextmanager
    def transaction(self):
        """ Start a series of git commands """
        self._transaction = Transaction()
        yield self._transaction
        self._transaction = None


    def get_config(self, name):
        """ Get a git config value.
        Return None if not found

        """
        (status, out) = self.config("--get", name, raises=False)
        if status != 0:
            return None
        return out.strip()

    def set_config(self, name, value):
        """ Set a new config value.
        Will be created if it does not exist
        """
        self.config(name, value)

    def get_current_ref(self, ref="HEAD"):
        """ return the current ref
        git symbolic-ref HEAD
        else: git name-rev --name-only --always HEAD
        """
        (status, out) = self.call("symbolic-ref", ref, raises=False)
        lines = out.splitlines()
        if len(lines) < 1:
            return None
        if status != 0:
            return None
        return lines[0]

    def get_current_branch(self):
        """ return the current branch """
        branch = self.get_current_ref()
        if not branch:
            return branch
        return branch[11:]


    def get_tracking_branch(self, branch=None):
        if not branch:
            branch = self.get_current_branch()

        remote = self.get_config("branch.%s.remote" % branch)
        merge  = self.get_config("branch.%s.merge" % branch)
        if not remote:
            return None
        if not merge:
            return None
        if merge.startswith("refs/heads/"):
            return "%s/%s" % (remote, merge[11:])
        return "%s/%s" % (remote, merge)

    def __getattr__(self, name):
        """Generate generic wrapper for call."""
        # If you want to specialize one, remove it from whitelist and write it
        # by hand (see clone).
        # Only porcelain here.
        whitelist = ("add", "branch", "checkout", "clean", "commit", "config",
                     "diff", "fetch", "init", "log", "merge", "pull", "push",
                     "rebase", "remote", "reset", "stash",
                     "status", "submodule")
        if name in whitelist:
            return functools.partial(self.call, name)
        raise AttributeError("Git instance has no attribute '%s'" % name)

    def clone(self, *args, **kwargs):
        """ Wrapper for git clone """
        args = list(args)
        args.append(self.repo)
        kwargs["cwd"] = None
        return self.call("clone", *args, **kwargs)

    def update_submodules(self, raises=True):
        """ Update submodule, cloning them if necessary """
        # This will fail if some pushed a broken submodule
        # (ie git metadata does not match .gitmodules)
        res, out = self.submodule("status", raises=False)
        if res != 0:
            mess  = "Broken submodules configuration detected for %s\n" % self.repo
            mess += "git status returned %s\n" % out
            if raises:
                raise Exception(mess)
            else:
                return mess
        if not out:
            return
        res, out = self.submodule("update", "--init", "--recursive",
                            raises=False)
        if res == 0:
            return
        mess  = "Failed to update submodules\n"
        mess += out
        if raises:
            raise Exception(mess)
        return mess


    def get_local_branches(self):
        """ Get the list of the local branches in a dict
        master -> tracking branch

        """
        (status, out) = self.branch("--no-color", raises=False)
        if status != 0:
            mess  = "Could not get the list of local branches\n"
            mess += "Error was: %s" % out
            raise Exception(mess)
        lines = out.splitlines()
        # Remove the star and the indentation:
        return [x[2:] for x in lines]

    def is_valid(self):
        """Check if the worktree is a valid git tree."""
        if not os.path.isdir(self.repo):
            return False
        (status, out) = self.call("rev-parse", "--is-inside-work-tree", raises=False)
        return status == 0

    def require_clean_worktree(self):
        """ Taken from /usr/lib/git-core/git-sh-setup
        return a tuple (bool, message) so that you can be more verbose
        in case the worktree is not clean

        """
        message = ""
        self.call("update-index", "--ignore-submodules", "--refresh", raises=False)
        out, _ = self.call("diff-files", "--quiet", "--ignore-submodules", raises=False)
        unstaged = False
        if out != 0:
            message = "You have unstaged changes"
            unstaged = True
        out, _ = self.call("diff-index", "--cached", "--ignore-submodules","HEAD",
                           raises = False)
        if out != 0:
            if unstaged:
                message += "Additionally, your index contains uncommited changes"
            else:
                message = "Your index contains uncommited changes"
        if message:
            return False, message
        else:
            return True, ""

    def get_status(self, untracked=True):
        """Return the output of status or None if it failed."""
        if untracked:
            (status, out) = self.status("--porcelain", raises=False)
        else:
            (status, out) = self.status("--porcelain", "--untracked-files=no",
                                                            raises=False)

        return out if status == 0 else None

    def is_clean(self, untracked=True):
        """
        Returns true if working dir is clean.
        (ie no untracked files, no unstaged changes)

            :param untracked: will return True even if there are untracked files.
        """
        out = self.get_status(untracked)
        if out is None:
            return None

        lines = [l for l in out.splitlines() if len(l.strip()) != 0]
        if len(lines) > 0:
            return False
        return True

    def is_empty(self):
        """ Returns true if there are no commit yet (between `git init` and
        `git commit`

        """
        rc, _ = self.call("rev-parse", "--verify", "HEAD", raises=False)
        return rc != 0


    def set_remote(self, name, url):
        """
        Set a new remote with the given name and url

        """
        # If it is already here, do nothing:
        in_conf = self.get_config("remote.%s.url" % name)
        if in_conf and in_conf == url:
            return
        self.remote("rm",  name, quiet=True, raises=False)
        self.remote("add", name, url, quiet=True)

    def branch_exists(self, name):
        rc, _ = self.call("show-ref", "--verify", "refs/heads/%s" % name, raises=False)
        return rc == 0

    def set_tracking_branch(self, branch, remote_name, remote_branch=None):
        """ Update the configuration of a branch to track
        a given remote branch

        :param branch: the branch to set configuration for
        :param remote_name: the name of the remove ('origin' in most cases)
        :param remote_branch: the name of the remote to track. If not given
            will be the same of the branch name
        """
        if remote_branch is None:
            remote_branch = branch
        if self.is_empty():
            raise Exception("repo in %s has no commit yet" % self.repo)
        if not self.branch_exists(branch):
            self.branch(branch)
        self.set_config("branch.%s.remote" % branch, remote_name)
        self.set_config("branch.%s.merge" % branch,
                        "refs/heads/%s" % remote_branch)

    def sync_branch(self, branch):
        """ git pull --rebase on steroids:

         * do not try anything if the worktree is not clean

         * update submodules and detect broken submodules configs

         * if no development occurred (master == origin/master),
           reset the local branch next to the remote
           (don't try to rebase, maybe there was a push -f)

         * if on the correct branch, rebase it

        Return a tuple (status, message), where status can be:
            - None: sync was skipped, but there was no error
            - False: sync failed
            - True: sync succeeded
        """
        remote_branch = branch.remote_branch
        if not remote_branch:
            remote_branch = branch.name
        remote_ref = "%s/%s" % (branch.tracks, remote_branch)

        if branch.tracks:
            fetch_cmd = ("fetch", branch.tracks)
        else:
            fetch_cmd = ("fetch")

        ok, mess = self.require_clean_worktree()
        if not ok:
            return None, mess

        rc, out = self.diff(branch.name, remote_ref, raises=False)
        if rc == 0 and not out:
            # No development was made on this branch: use reset --hard
            update_cmd = ("reset", "--hard", remote_ref)
        else:
            if branch.tracks:
                update_cmd = ("rebase", remote_ref, branch.name)
            else:
                # This may fail depending on the user configuration
                update_cmd = ("rebase", branch.name)

        update_successful = False
        message = ""
        with self.transaction() as transaction:
            self.call(*fetch_cmd)
            (rc, out) = self.call(*update_cmd)
            if rc == 0:
                update_successful = True
            else:
                if update_cmd[0] == "rebase":
                    # run rebase --abort so that the user is left
                    # in a clean state, making sure we
                    # continue the transaction even if last command failed
                    transaction.ok = True
                    message = "Rebase failed because of conflicts"
                    self.call("rebase", "--abort")

        if transaction.ok:
            return update_successful, message
        else:
            return False, transaction.output

    def is_ff(self, local_sha1, remote_sha1):
        """Check local_sha1 is fast-forward with remote_sha1.
        Return True / False or None in case of error with merge-base.
        """
        (retcode, out) = self.call("merge-base", local_sha1, remote_sha1,
                                   raises=False)
        if retcode != 0:
            ui.error("Calling merge-base failed")
            ui.error(out)
            return
        else:
            common_ancestor = out.strip()
            return common_ancestor == local_sha1

    def get_ref_sha1(self, ref):
        """Return the sha1 from a ref. None if not found."""
        (ret, sha1) = self.call("show-ref", "--verify", "--hash",
                               ref, raises=False)

        if ret == 0:
            return sha1

    def sync_branch_devel(self, local_branch, master_branch):
        """ Make sure master stays compatible with your development branch
        Checks if your local master branch can be fast-forwarded to remote
        Update master's HEAD if it's the case
        """

        if master_branch.tracks:
            fetch_cmd = ("fetch", master_branch.tracks)
        else:
            fetch_cmd = ("fetch")
        self.call(*fetch_cmd)

        # First check if master can be fast-forwarded
        local_sha1 = self.get_ref_sha1("refs/heads/%s" % master_branch.name)
        if local_sha1 is None:
            return

        remote_ref = "refs/remotes/%s/%s" % \
                     (master_branch.tracks, master_branch.name)
        remote_sha1 = self.get_ref_sha1(remote_ref)

        if remote_sha1 is None:
            return

        if local_sha1 == remote_sha1:
            # Nothing to do, we're good
            return True, ""
        result_ff = self.is_ff(local_sha1, remote_sha1)
        if result_ff:
            ui.info("Branch %s can be fast-forwarded" % master_branch.name)
        else:
            return True, "Branch %s isn't fast-forward" % master_branch.name

        # update master HEAD ref (only because we're fast-forward /!\)
        reason = "qisrc Fast-forward to %s" % remote_sha1
        master_head = "refs/heads/%s" % master_branch.name
        self.call("update-ref", "-m", reason, master_head,
        remote_sha1, local_sha1)
        return True, "Fast-forwarded %s. Feel free to rebase on %s" % \
                                        ((master_branch.name,) * 2)


    def __repr__(self):
        return "<Git repo in %s>" % self.repo



def get_repo_root(path):
    """Return the root dir of a git worktree given a path.

    :return None: if it's not a git work tree.
    """
    if os.path.isfile(path):
        path = os.path.dirname(path)
    if not os.path.isdir(path):
        return None

    git = Git(path)
    (ret, out) = git.call("rev-parse", "--show-toplevel", raises=False)

    return out.replace('/', os.sep) if ret == 0 else None

def is_submodule(path):
    """ Tell if the given path is a submodule

    """
    if not os.path.isdir(path):
        return False

    # Two cases:
    # * submodule not initialized -> path will be an empty dir
    # * submodule initialized  -> path/.git will be a file
    #   looking like:
    #       gitdir: ../../.git/modules/bar
    contents = os.listdir(path)
    if contents:
        dot_git = os.path.join(path, ".git")
        if os.path.isdir(dot_git):
            return False
        parent_repo_root = get_repo_root(os.path.dirname(path))
    else:
        parent_repo_root = get_repo_root(path)
    parent_git = Git(parent_repo_root)
    (retcode, out) = parent_git.submodule(raises=False)
    if retcode == 0:
        if not out:
            return False
        else:
            lines = out.splitlines()
            submodules = [x.split()[1] for x in lines]
            rel_path = os.path.relpath(path, parent_repo_root)
            return rel_path in submodules
    else:
        ui.warning("git submodules configuration is broken for",
                   parent_repo_root, "!",
                   "\nError was: ", ui.reset, "\n", "  " + out)
        return True

def is_git(path):
    """Return true if path is in a git work-tree."""
    return get_repo_root(path) == path

def name_from_url(url):
    """ Return the project name from the url
    Assume there project name is always in the form
    "foo/bar.git"

    >>> name_from_url("git@git:foo/bar.git")
    'foo/bar.git'

    """
    if url.startswith("file://"):
        sep = "/"
        if os.name == 'nt' and "\\"  in url:
            sep = "\\"
        return url.split(sep)[-1]

    if "://" in url:
        url = url.split("://", 1)[-1]
        if ":" in url:
            port_and_rest = url.split(":")[-1]
            return port_and_rest.split("/", 1)[-1]
        else:
            return url.split("/", 1)[-1]
    else:
        if ":" in url:
            return url.split(":")[-1]
        else:
            return url.split("/")[-1]


class Transaction:
    """ Used to simplify chaining git commands """
    def __init__(self):
        self.ok = True
        self.output = ""
