(define (domain orbiter)

  (:requirements :strips :typing :durative-actions)

  (:types
    target
  )

  (:predicates
    ;; Mission state, one fact per target.
    (imaged ?t - target)     ; a raw image of the target is in onboard storage
    (processed ?t - target)  ; the image has been turned into a downlinkable product

    ;; Equipment state. The satellite carries one camera and one processor.
    (camera-free)
    (processor-free)
  )

  ;; Point the satellite at a target and take an image.
  (:durative-action observe
    :parameters (?t - target)
    :duration (= ?duration 5)
    :condition (over all (camera-free))
    :effect (at end (imaged ?t))
  )

  ;; Turn a raw image into a downlinkable product.
  ;; The processor is claimed at start and released at end.
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
)
