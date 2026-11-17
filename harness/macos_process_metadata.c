/* Diagnostic-only macOS process metadata. No injection or private linking.
 * Responsibility uses an OPTIONAL dynamically resolved private OS symbol.
 * Failure to resolve is explicitly reported; do not infer attribution.
 * Input: one PID per line. Output: header + TSV fields for each PID.
 */
#include <dlfcn.h>
#include <errno.h>
#include <libproc.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/resource.h>
#include <sys/types.h>

typedef pid_t (*responsible_pid_fn)(pid_t);

int main(void) {
    responsible_pid_fn responsible = (responsible_pid_fn)dlsym(RTLD_DEFAULT,
                           "responsibility_get_pid_responsible_for_pid");
    void *optional_library = NULL;
    if (responsible == NULL) {
        optional_library = dlopen("/usr/lib/libresponsibility.dylib", RTLD_LAZY);
        if (optional_library != NULL) {
            responsible = (responsible_pid_fn)dlsym(optional_library,
                               "responsibility_get_pid_responsible_for_pid");
        }
    }
    printf("pid\tresponsible_pid\tresident_bytes\tphysical_footprint_bytes\trusage_status\n");
    fflush(stdout);
    char line[80];
    while (fgets(line, sizeof(line), stdin) != NULL) {
        errno = 0;
        char *end = NULL;
        long parsed = strtol(line, &end, 10);
        if (errno != 0 || end == line || parsed <= 0 || parsed > INT32_MAX ||
            (*end != '\n' && *end != '\0')) {
            fprintf(stderr, "invalid input PID: %s", line);
            return 2;
        }
        pid_t pid = (pid_t)parsed;
        pid_t answer = responsible == NULL ? -1 : responsible(pid);
        if (answer <= 0) answer = -1;
        struct rusage_info_v2 usage = {0};
        int ok = proc_pid_rusage(pid, RUSAGE_INFO_V2, (rusage_info_t)&usage);
        if (ok == 0) {
            printf("%d\t%d\t%llu\t%llu\tok\n", pid, answer,
                   (unsigned long long)usage.ri_resident_size,
                   (unsigned long long)usage.ri_phys_footprint);
        } else {
            printf("%d\t%d\t-1\t-1\tunavailable\n", pid, answer);
        }
        fflush(stdout);
    }
    if (optional_library != NULL) dlclose(optional_library);
    return 0;
}
