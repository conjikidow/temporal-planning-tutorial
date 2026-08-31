(define (domain orbiter)

  (:requirements :strips :typing :durative-actions)

  (:types
    target
  )

  (:predicates
    ;; Mission state, one fact per target.
    (imaged ?t - target)      ; a raw image of the target is in onboard storage
    (processed ?t - target)   ; the image has been turned into a downlinkable product
    (downlinked ?t - target)  ; the product has reached the ground

    ;; Equipment state. The satellite carries one of each.
    (camera-free)
    (processor-free)
    (transmitter-free)

    ;; Environment state. Orbital geometry decides this, not the satellite, so no action ever claims or releases it.
    (primary-visible)  ; the high-rate ground station is in view
  )

  ;; Point the satellite at a target and take an image.
  ;; The camera is claimed at start and released at end, so two observations cannot overlap.
  (:durative-action observe
    :parameters (?t - target)
    :duration (= ?duration 5)
    :condition (at start (camera-free))
    :effect (and
      (at start (not (camera-free)))
      (at end (camera-free))
      (at end (imaged ?t))
    )
  )

  ;; Turn a raw image into a downlinkable product.
  ;; The processor is claimed at start and released at end, so two runs cannot overlap.
  (:durative-action process
    :parameters (?t - target)
    :duration (= ?duration 2)
    :condition (and
      (at start (processor-free))
      (over all (imaged ?t))
    )
    :effect (and
      (at start (not (processor-free)))
      (at end (processor-free))
      (at end (processed ?t))
    )
  )

  ;; Transmit the processed product of one target over the high-rate link.
  ;; This is fast, but it only works while the primary ground station is in view.
  (:durative-action downlink
    :parameters (?t - target)
    :duration (= ?duration 3)
    :condition (and
      (at start (transmitter-free))
      (over all (processed ?t))
      (over all (primary-visible))
    )
    :effect (and
      (at start (not (transmitter-free)))
      (at end (transmitter-free))
      (at end (downlinked ?t))
    )
  )

  ;; Transmit the same product over the low-rate backup link, which is always reachable.
  ;; It needs no ground station in view, and takes three times as long.
  ;; Both links share the one transmitter.
  (:durative-action downlink-backup
    :parameters (?t - target)
    :duration (= ?duration 9)
    :condition (and
      (at start (transmitter-free))
      (over all (processed ?t))
    )
    :effect (and
      (at start (not (transmitter-free)))
      (at end (transmitter-free))
      (at end (downlinked ?t))
    )
  )
)
